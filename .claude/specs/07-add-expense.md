# Spec: Add Expense

## Overview
This feature implements the add-expense form, allowing a logged-in user to record a new expense with an amount, date, description, and category. It replaces the Step 7 stub route with a fully working GET/POST handler, a `db.py` helper for inserting records, and a dedicated template. This is the first write path for expense data and is a prerequisite for the edit and delete steps that follow.

## Depends on
- Step 01 — Database setup (expenses and categories tables must exist)
- Step 02 — Registration (user accounts)
- Step 03 — Login and Logout (session + `login_required` decorator)

## Routes
- `GET /expenses/add` — render the add-expense form, populated with the user's categories — logged-in
- `POST /expenses/add` — validate and insert a new expense, then redirect to `/profile` — logged-in

## Database changes
No new tables or columns. The `expenses` table already has all required columns (`user_id`, `category_id`, `amount`, `date`, `description`). Two new helper functions are added to `database/db.py`:
- `get_categories(user_id)` — returns all categories for a user
- `add_expense(user_id, category_id, amount, date, description)` — inserts one expense row

## Templates
- **Create:** `expense-tracker/templates/add_expense.html` — form with fields: amount (number), date (date), description (text), category (select populated from DB), and a submit button
- **Modify:** `expense-tracker/templates/base.html` — add "Add Expense" nav link pointing to `url_for('add_expense')`, visible only when logged in

## Files to change
- `expense-tracker/app.py` — replace the stub `add_expense` route with GET/POST handler; add `@login_required`
- `expense-tracker/database/db.py` — add `get_categories()` and `add_expense()` helpers
- `expense-tracker/templates/base.html` — add nav link for Add Expense

## Files to create
- `expense-tracker/templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with werkzeug (not relevant here but must not be broken)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic lives in `database/db.py` only — no inline SQL in route functions
- Route function has one responsibility: validate input, call db helper, redirect or re-render
- `category_id` is optional — if the user submits no category, store `NULL`
- `amount` must be a positive number; `date` must be a valid YYYY-MM-DD string
- On validation failure, re-render the form with an inline error message and preserve entered values
- On success, flash a success message and redirect to `url_for('profile')`

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login` with a flash message
- [ ] Visiting `/expenses/add` while logged in renders a form with Amount, Date, Description, and Category fields
- [ ] The Category dropdown is populated with the logged-in user's categories (e.g. Food, Travel, Bills, Entertainment)
- [ ] Submitting the form with valid data creates a new row in the `expenses` table and redirects to `/profile`
- [ ] The profile page stats (count and total) increase by the correct values after adding an expense
- [ ] Submitting with a missing or zero amount shows a validation error and does not insert a row
- [ ] Submitting with a missing date shows a validation error and does not insert a row
- [ ] Category field is optional — submitting without selecting a category stores `NULL` for `category_id`
- [ ] The "Add Expense" nav link in `base.html` is visible when logged in and navigates to `/expenses/add`
