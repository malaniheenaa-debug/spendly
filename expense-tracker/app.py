import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from database.db import init_db, get_db

DEFAULT_CATEGORIES = ["Food", "Travel", "Bills", "Entertainment"]

app = Flask(__name__)
app.secret_key = "dev-secret-key"

with app.app_context():
    init_db()


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


@app.route("/login")
def login():
    return render_template("login.html")


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
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
