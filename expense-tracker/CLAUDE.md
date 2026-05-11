# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the development server (port 5001)
python app.py

# Run tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run tests with output
pytest -v
```

The app requires a `venv` — activate it before running:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

## Architecture

**Spendly** is a Flask expense-tracker web app backed by SQLite. The project is structured as a step-by-step student exercise; many routes are stubs that students fill in.

### Key files

- `app.py` — All Flask routes. Currently has live routes for landing, register, login, terms, privacy; stub routes for logout, profile, and expense CRUD.
- `database/db.py` — SQLite helper (students implement): `get_db()` returns a connection with `row_factory` and foreign keys enabled; `init_db()` creates tables; `seed_db()` inserts sample data.
- `templates/base.html` — Shared layout: navbar with dark/light toggle, footer with Terms/Privacy links. All other templates extend this.
- `static/js/main.js` — Theme toggle only; persists choice in `localStorage` under key `spendly-theme`. Dark mode is activated by setting `data-theme="dark"` on `<html>`.
- `static/css/style.css` — Global styles (used by all pages via `base.html`).
- `static/css/landing.css` — Landing-page-specific styles.

### Template pattern

All pages extend `base.html` and fill `{% block title %}`, `{% block head %}` (extra CSS/JS), `{% block content %}`, and optionally `{% block scripts %}`.

### Database conventions (for when `db.py` is implemented)

- Use `sqlite3` with `row_factory = sqlite3.Row` so rows are dict-like.
- Enable foreign keys with `PRAGMA foreign_keys = ON` in `get_db()`.
- Schema created with `CREATE TABLE IF NOT EXISTS`.

### Planned step progression

Routes marked "coming in Step N" in `app.py` indicate the order students will implement features:
- Step 1: Database setup (`database/db.py`)
- Step 3: Auth (login/logout/session)
- Step 4: User profile
- Steps 7–9: Expense add / edit / delete
