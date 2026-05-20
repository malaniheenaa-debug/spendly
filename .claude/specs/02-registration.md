# Spec: Step 2 — Registration

## Goal

Implement user registration: a POST `/register` handler that validates form input, hashes the password, inserts a new user into the database, seeds their default categories, and redirects to the login page.

---

## What already exists

- `templates/register.html` — form with `name`, `email`, and `password` fields, POSTs to `/register`, renders `{{ error }}` if set.
- `app.py` — GET `/register` renders the template; stub POST handler not yet implemented.
- `database/db.py` — `get_db()` returns a connection with `row_factory = sqlite3.Row`; `init_db()` creates `users` and `categories` tables.
- `app.py` — `DEFAULT_CATEGORIES = ["Food", "Travel", "Bills", "Entertainment"]` defined at module level.

---

## What to implement

### 1. POST `/register` handler in `app.py`

```
POST /register
  Body: name, email, password (form fields)
```

**Imports to add:** `generate_password_hash` from `werkzeug.security`; `sqlite3` (for `IntegrityError`).

**Validation — re-render `register.html` with `error=<message>` on first failure:**

| Field    | Rule                              | Error message                          |
|----------|-----------------------------------|----------------------------------------|
| name     | non-empty after strip             | `"Name is required."`                  |
| email    | non-empty after strip, contains @ | `"A valid email is required."`         |
| password | non-empty, length ≥ 8             | `"Password must be at least 8 characters."` |

**Happy path:**
1. Strip whitespace from `name` and `email`; do not strip `password`.
2. Validate in the order above; return on first failure.
3. Hash password with `generate_password_hash(password)`.
4. Open a DB connection and `INSERT INTO users (name, email, password) VALUES (?, ?, ?)`.
5. Capture `cursor.lastrowid` as `user_id`.
6. Bulk-insert default categories: `INSERT INTO categories (user_id, name) VALUES (?, ?)` for each entry in `DEFAULT_CATEGORIES`.
7. `conn.commit()`.
8. Flash `"Account created — please sign in."` (category `"success"`).
9. Redirect to `url_for("login")`.

**Duplicate email:** catch `sqlite3.IntegrityError` and re-render with `error="An account with that email already exists."`.

Always close the connection in a `finally` block.

---

## Files to modify

| File    | Change |
|---------|--------|
| `app.py` | Add POST handling to `/register` route |

`database/db.py` and `templates/register.html` — **no changes needed**.

---

## Validation rules (summary)

Validate in this order; return on the first failure:

1. `name` non-empty after strip → `"Name is required."`
2. `email` non-empty after strip and contains `@` → `"A valid email is required."`
3. `password` non-empty and `len >= 8` → `"Password must be at least 8 characters."`
4. Duplicate email (IntegrityError) → `"An account with that email already exists."`

---

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3`
- Parameterised queries only — no string formatting into SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

---

## Verification

1. Visit `/register` — page renders with name/email/password form.
2. Submit empty form → error `"Name is required."`
3. Submit name only, empty email → error `"A valid email is required."`
4. Submit name + email, password < 8 chars → error `"Password must be at least 8 characters."`
5. Submit valid details → redirected to `/login`, flash `"Account created — please sign in."` visible.
6. Submit same email again → error `"An account with that email already exists."`
7. Check the database — new row exists in `users`; four rows exist in `categories` for that `user_id`.
