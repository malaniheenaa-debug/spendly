
# Spec: Backend Routes for Profile Page

## Overview

Wire up the profile page with real backend logic. This step implements:

1. The `@login_required` decorator — protects all authenticated routes
2. `POST /login` — verifies credentials and creates a session
3. `GET /logout` — clears the session and redirects to login
4. `GET /profile` — queries the DB for user info and expense stats, renders `profile.html`

After this step, a user can register, sign in, view their profile with real data, and sign out. This is the foundation all expense routes (Steps 7–9) depend on.

## Depends on

- Step 1: Database setup (`database/db.py` — `get_db()`, `users` and `expenses` tables)
- Step 2: Registration (user rows exist in `users` with hashed passwords)
- Step 4: Profile page design (`templates/profile.html` and `static/css/profile.css` already exist)

## Routes

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| `POST` | `/login` | No | Verify credentials, create session, redirect to `/profile` |
| `GET` | `/logout` | No | Clear session, redirect to `/login` |
| `GET` | `/profile` | Yes | Render profile page with user info and expense stats |

The existing `GET /login` route stays unchanged (renders the form).

## Database changes

None. All required columns already exist:
- `users`: `id`, `name`, `email`, `password`, `created_at`
- `expenses`: `id`, `user_id`, `amount`

## Files to change

- `expense-tracker/app.py`
  - Add `login_required` decorator function
  - Add `check_password_hash` to the werkzeug import
  - Add `session` to the Flask import
  - Replace the `GET /login` stub with a `GET, POST` handler
  - Replace the `GET /logout` stub with a real implementation
  - Replace the `GET /profile` stub with a real DB query + `render_template`

## Files to create

None. Templates and CSS already exist from Step 4.

## New dependencies

None.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` with parameterised queries only
- Passwords verified with `check_password_hash` — never compare plain text
- Session keys: `session["user_id"]` (int) and `session["user_name"]` (str)
- Use `flash()` for all user-facing messages
- Close the DB connection in a `finally` block
- `@login_required` must redirect to `/login` with a flash message on failure, not raise 403

## Implementation detail

### 1. Imports (top of `app.py`)

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
```

### 2. `login_required` decorator

Add this **before** any route definitions:

```python
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated
```

### 3. `GET /login` → `GET, POST /login`

Replace the existing stub:

```python
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

    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    flash(f"Welcome back, {user['name']}!", "success")
    return redirect(url_for("profile"))
```

### 4. `GET /logout`

Replace the existing stub:

```python
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))
```

### 5. `GET /profile`

Replace the existing stub:

```python
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
```

## Definition of done

- [ ] `GET /login` renders the login form (no regression)
- [ ] `POST /login` with correct credentials → session set, redirected to `/profile`, flash "Welcome back"
- [ ] `POST /login` with wrong password → stays on login form, shows "Incorrect email or password."
- [ ] `POST /login` with unknown email → same error as wrong password (no user-enumeration leak)
- [ ] `GET /logout` → session cleared, redirected to `/login`, flash "You have been signed out."
- [ ] `GET /profile` without session → redirected to `/login` with flash "Please sign in to continue."
- [ ] `GET /profile` with session → renders `profile.html` with correct name, email, and "Member since" date
- [ ] Stats grid shows correct expense count and total (verify with seed data or manual DB check)
- [ ] A user with zero expenses sees count `0` and total `₹0.00` (no crash)
- [ ] Navbar shows user's name and "Sign out" link when logged in
- [ ] Navbar shows "Sign in" / "Get started" links when logged out
