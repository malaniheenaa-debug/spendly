---
name: project-spendly-domain
description: Core domain facts about the Spendly Flask app — schema, routes, auth pattern, and test conventions discovered from the codebase.
metadata:
  type: project
---

Spendly is a Flask expense tracker backed by SQLite with three tables: `users`, `categories`, `expenses`.

**Schema highlights**
- `expenses.date` is stored as a `DATE` string in `YYYY-MM-DD` format (SQLite text comparison).
- `categories` are per-user; the default set is Food, Travel, Bills, Entertainment.
- Foreign keys are enabled via `PRAGMA foreign_keys = ON` in `get_db()`.
- `get_db()` lives in `database/db.py` and returns a `sqlite3.Row`-factory connection.

**Auth pattern**
- `login_required` decorator checks `session["user_id"]`; missing → redirect to `/login`.
- Session also stores `session["user_name"]` (used in template greetings).

**Profile sub-routes (Step 06)**
- `/profile/history` — expense table, filterable by `?from=` and `?to=`.
- `/profile/stats` — aggregate stats; no params → This Month + All Time; any date param → Filtered Period only.
- `/profile/categories` — category totals + grand total, filterable by date.
- `_parse_date_params()` in `app.py` validates both params against `^\d{4}-\d{2}-\d{2}$`; returns `(None, None)` and flashes "Invalid date format — use YYYY-MM-DD." on mismatch.

**Why:** Reference so future test generation doesn't need to re-read the source.
**How to apply:** Use these facts to write business-rule assertions (date boundary inclusivity, per-user isolation, flash message text, section heading names).
