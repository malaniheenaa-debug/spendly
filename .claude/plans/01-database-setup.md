# Plan: Step 1 — Database Setup

## Context

`database/db.py` is currently a stub (comments only). Step 1 requires implementing three functions that all later steps depend on: `get_db()` for acquiring a connection, `init_db()` for creating the schema, and `seed_db()` for populating development data. `app.py` also needs a minimal wiring change to call `init_db()` at startup so the DB is ready when the app boots.

---

## Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| email | TEXT | NOT NULL UNIQUE |
| password | TEXT | NOT NULL (hashed) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### `categories`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | FK → users(id) ON DELETE CASCADE |
| name | TEXT | NOT NULL |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### `expenses`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | FK → users(id) ON DELETE CASCADE |
| category_id | INTEGER | FK → categories(id) ON DELETE SET NULL |
| amount | REAL | NOT NULL |
| date | DATE | NOT NULL |
| description | TEXT | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

---

## Files Modified

- `expense-tracker/database/db.py` — full implementation
- `expense-tracker/app.py` — added `init_db` import, `secret_key`, and startup call

---

## Verification

1. Run `python app.py` — app boots without errors; `database/spendly.db` is created.
2. Python shell: `from database.db import get_db; conn = get_db(); print(list(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()))` — should list `users`, `categories`, `expenses`.
3. Run `from database.db import seed_db; seed_db()` — then query to confirm 1 user, 4 categories, 6 expenses.
4. Foreign key test: insert an expense with a non-existent `user_id` and expect `IntegrityError`.
