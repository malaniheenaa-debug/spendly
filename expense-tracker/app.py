import re
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, get_db

DEFAULT_CATEGORIES = ["Food", "Travel", "Bills", "Entertainment"]

app = Flask(__name__)
app.secret_key = "dev-secret-key"

with app.app_context():
    init_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name:
        return render_template("register.html", error="Name is required.")
    if not email or "@" not in email:
        return render_template("register.html", error="A valid email is required.")
    if not password or len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    hashed = generate_password_hash(password)
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed),
        )
        user_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)",
            [(user_id, cat) for cat in DEFAULT_CATEGORIES],
        )
        conn.commit()
        response = redirect(url_for("login"))
        flash("Account created — please sign in.", "success")
    except sqlite3.IntegrityError:
        response = render_template(
            "register.html",
            error="An account with that email already exists.",
        )
    finally:
        conn.close()
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="Email and password are required.")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, password FROM users WHERE email = ?",
            (email,)
        ).fetchone()
    finally:
        conn.close()

    if user is None or not check_password_hash(user["password"], password):
        return render_template("login.html", error="Incorrect email or password.")

    session.clear()
    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    flash(f"Welcome back, {user['name']}!", "success")
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()
        stats = conn.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?",
            (session["user_id"],)
        ).fetchone()
    finally:
        conn.close()
    return render_template("profile.html", user=user, stats=stats)


_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _parse_date_params():
    from_date = request.args.get("from", "").strip() or None
    to_date   = request.args.get("to",   "").strip() or None
    for val in (from_date, to_date):
        if val and not _DATE_RE.match(val):
            flash("Invalid date format — use YYYY-MM-DD.", "error")
            return None, None
    return from_date, to_date


# ------------------------------------------------------------------ #
# SECTION A: Transaction History — Subagent 1                        #
# ------------------------------------------------------------------ #
@app.route("/profile/history")
@login_required
def transaction_history():
    from_date, to_date = _parse_date_params()
    conn = get_db()
    try:
        expenses = conn.execute(
            """
            SELECT e.id, e.amount, e.date, e.description,
                   COALESCE(c.name, 'Uncategorised') AS category
            FROM expenses e
            LEFT JOIN categories c ON c.id = e.category_id
            WHERE e.user_id = ?
              AND (? IS NULL OR e.date >= ?)
              AND (? IS NULL OR e.date <= ?)
            ORDER BY e.date DESC, e.id DESC
            """,
            (session["user_id"], from_date, from_date, to_date, to_date)
        ).fetchall()
    finally:
        conn.close()
    return render_template(
        "history.html",
        expenses=expenses,
        user_name=session["user_name"],
        from_date=from_date,
        to_date=to_date,
    )


# ------------------------------------------------------------------ #
# SECTION B: Summary Stats — Subagent 2                              #
# ------------------------------------------------------------------ #
@app.route("/profile/stats")
@login_required
def summary_stats():
    from_date, to_date = _parse_date_params()
    conn = get_db()
    try:
        if from_date or to_date:
            filtered = conn.execute(
                """
                SELECT COUNT(*) AS count,
                       COALESCE(SUM(amount), 0) AS total,
                       COALESCE(AVG(amount), 0) AS avg,
                       COALESCE(MAX(amount), 0) AS biggest
                FROM expenses
                WHERE user_id = ?
                  AND (? IS NULL OR date >= ?)
                  AND (? IS NULL OR date <= ?)
                """,
                (session["user_id"], from_date, from_date, to_date, to_date)
            ).fetchone()
            all_time   = None
            this_month = None
        else:
            filtered = None
            all_time = conn.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total, COALESCE(AVG(amount), 0) AS avg, COALESCE(MAX(amount), 0) AS biggest FROM expenses WHERE user_id = ?",
                (session["user_id"],)
            ).fetchone()
            this_month = conn.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')",
                (session["user_id"],)
            ).fetchone()
    finally:
        conn.close()
    return render_template(
        "stats.html",
        all_time=all_time,
        this_month=this_month,
        filtered=filtered,
        user_name=session["user_name"],
        from_date=from_date,
        to_date=to_date,
    )


# ------------------------------------------------------------------ #
# SECTION C: Category Breakdown — Subagent 3                         #
# ------------------------------------------------------------------ #
@app.route("/profile/categories")
@login_required
def category_breakdown():
    from_date, to_date = _parse_date_params()
    conn = get_db()
    try:
        categories = conn.execute(
            """
            SELECT c.name,
                   COUNT(e.id)                AS count,
                   COALESCE(SUM(e.amount), 0) AS total
            FROM categories c
            LEFT JOIN expenses e
                   ON e.category_id = c.id
                  AND e.user_id = ?
                  AND (? IS NULL OR e.date >= ?)
                  AND (? IS NULL OR e.date <= ?)
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY total DESC
            """,
            (session["user_id"], from_date, from_date, to_date, to_date, session["user_id"])
        ).fetchall()
        grand_total = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = ?
              AND (? IS NULL OR date >= ?)
              AND (? IS NULL OR date <= ?)
            """,
            (session["user_id"], from_date, from_date, to_date, to_date)
        ).fetchone()
    finally:
        conn.close()
    return render_template(
        "categories.html",
        categories=categories,
        grand_total=grand_total["total"],
        user_name=session["user_name"],
        from_date=from_date,
        to_date=to_date,
    )


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
