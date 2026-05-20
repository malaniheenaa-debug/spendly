# Spec: Step 3 — Login and Logout

## Goal

Implement session-based authentication: a POST `/login` handler that verifies credentials and stores a session, a `/logout` handler that clears it, and a `login_required` decorator to protect future routes.

---

## What already exists

- `templates/login.html` — form with `email` and `password` fields, POSTs to `/login`, renders `{{ error }}` if set.
- `app.py` — GET `/login` renders the template; `/logout` stub returns a placeholder string.
- `database/db.py` — `get_db()` returns a connection with `row_factory = sqlite3.Row`.
- `templates/base.html` — navbar always shows "Sign in" and "Get started"; flash messages already wired.
- `app.secret_key` is already set in `app.py`.

---

## What to implement

### 1. POST `/login` handler in `app.py`

```
POST /login
  Body: email, password (form fields)
```

**Happy path:**
1. Strip whitespace from `email`; do not strip `password`.
2. Validate — if any rule fails, re-render `login.html` with `error=<message>`:
   - `email` must be non-empty after strip (`"Email is required."`).
   - `password` must be non-empty (`"Password is required."`).
3. Query `SELECT * FROM users WHERE email = ?` with the stripped email.
4. If no row found, or `check_password_hash(row["password"], password)` returns `False`, re-render with `error="Invalid email or password."`.
5. On success: call `session.clear()`, then store `session["user_id"] = row["id"]` and `session["user_name"] = row["name"]`.
6. Redirect to `url_for("profile")` with flash `"Welcome back, {name}!"` (category `"success"`).

**Imports to add:** `check_password_hash` from `werkzeug.security`; `session` from `flask`.

---

### 2. `/logout` handler in `app.py`

Replace the placeholder string with:
1. `session.clear()`
2. Flash `"You've been signed out."` (category `"success"`).
3. Redirect to `url_for("login")`.

---

### 3. `login_required` decorator in `app.py`

Add a reusable decorator above the routes:

```python
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated
```

Apply `@login_required` to the `/profile` route only. Leave the stub expense routes as-is.

---

### 4. Navbar update in `base.html`

Replace the static "Sign in" / "Get started" links with session-conditional links:

```html
{% if session.get('user_id') %}
    <a href="{{ url_for('profile') }}">{{ session['user_name'] }}</a>
    <a href="{{ url_for('logout') }}" class="nav-cta">Sign out</a>
{% else %}
    <a href="{{ url_for('login') }}">Sign in</a>
    <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
{% endif %}
```

---

## Files to modify

| File | Change |
|---|---|
| `app.py` | Add POST to `/login`, implement `/logout`, add `login_required` decorator, apply to `/profile` |
| `templates/base.html` | Conditional navbar links based on `session.get('user_id')` |

`database/db.py` — **no changes needed**.

---

## Validation rules (summary)

| Field | Rule | Error message |
|---|---|---|
| email | non-empty after strip | "Email is required." |
| password | non-empty | "Password is required." |
| credentials | email exists and password matches | "Invalid email or password." |

Validate in the order above; return on the first failure. Use the same error for wrong email and wrong password — no user enumeration.

---

## Verification

1. Visit `/login` — page renders with email/password form.
2. Submit empty form → error "Email is required."
3. Submit valid email, empty password → error "Password is required."
4. Submit wrong email or wrong password → error "Invalid email or password." (same message for both).
5. Submit correct credentials → redirected to `/profile`, flash "Welcome back, {name}!" visible.
6. After login, navbar shows the user's name and a "Sign out" link.
7. Click "Sign out" → redirected to `/login`, flash "You've been signed out." visible.
8. After logout, visiting `/profile` directly → redirected to `/login`, flash "Please sign in to continue." visible.
