# Spec: Edit Expense

## Overview
This feature implements the edit-expense flow, allowing a logged-in user to update an existing expense's amount, date, description, and category. It replaces the Step 8 stub route with a fully working GET/POST handler, two new `db.py` helpers (`get_expense` and `update_expense`), and a dedicated edit form template. Ownership is enforced so users can only edit their own expenses.

## Depends on
- Step 01 — Database setup (expenses and categories tables must exist)
- Step 02 — Registration (user accounts)
- Step 03 — Login and Logout (session + `login_required` decorator)
- Step 07 — Add Expense (expenses exist to edit; categories populated)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the existing expense's data — logged-in
- `POST /expenses/<int:id>/edit` — validate and save the updated expense, then redirect to `/profile/history` — logged-in

## Database changes
No new tables or columns. The `expenses` table already has all required columns including `updated_at`. Two new helper functions are added to `database/db.py`:
- `get_expense(expense_id, user_id)` — fetches a single expense row, verifying it belongs to the given user; returns `None` if not found or not owned
- `update_expense(expense_id, user_id, category_id, amount, date, description)` — updates the row and sets `updated_at = CURRENT_TIMESTAMP`

## Templates
- **Create:** `expense-tracker/templates/edit_expense.html` — form with Amount, Date, Description, and Category fields pre-filled from the existing expense; extends `base.html`
- **Modify:** `expense-tracker/templates/history.html` — add an "Edit" link on each expense row pointing to `url_for('edit_expense', id=expense.id)`

## Files to change
- `expense-tracker/app.py` — replace the stub `edit_expense` route with a GET/POST handler; add `@login_required`; use `abort(404)` if the expense is not found or not owned by the current user
- `expense-tracker/database/db.py` — add `get_expense()` and `update_expense()` helpers
- `expense-tracker/templates/history.html` — add Edit link per row

## Files to create
- `expense-tracker/templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with werkzeug (must not be broken)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic lives in `database/db.py` only — no inline SQL in route functions
- Ownership check is mandatory: fetch expense with both `id` and `user_id`; call `abort(404)` if the result is `None`
- `category_id` is optional — if the user submits no category, store `NULL`
- `amount` must be a positive number; `date` must be a valid YYYY-MM-DD string
- On validation failure, re-render the form with an inline error message and preserve entered values
- On success, flash a success message and redirect to `url_for('transaction_history')`
- Set `updated_at = CURRENT_TIMESTAMP` in the UPDATE query

## Definition of done
- [ ] Visiting `/expenses/1/edit` while logged out redirects to `/login` with a flash message
- [ ] Visiting `/expenses/1/edit` while logged in as the owner renders a form pre-filled with the existing amount, date, description, and category
- [ ] Visiting `/expenses/1/edit` while logged in as a different user returns a 404
- [ ] The Category dropdown is populated with the logged-in user's categories
- [ ] Submitting the form with valid data updates the expense row in the database and redirects to `/profile/history`
- [ ] The updated values are visible in the transaction history after saving
- [ ] Submitting with a missing or zero amount shows a validation error and does not update the row
- [ ] Submitting with a missing or invalid date shows a validation error and does not update the row
- [ ] Category field is optional — submitting without selecting a category stores `NULL` for `category_id`
- [ ] The "Edit" link is visible on each row in `/profile/history` and navigates to the correct edit page
