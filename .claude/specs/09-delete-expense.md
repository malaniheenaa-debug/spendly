# Spec: Delete Expense

## Overview
This feature implements the delete-expense flow, allowing a logged-in user to permanently remove one of their own expenses. It replaces the Step 9 stub route with a GET confirmation page and a POST delete handler, a new `delete_expense` db helper, and a confirmation template. Ownership is enforced so users can only delete their own expenses. A Delete button is added beside the existing Edit link in the transaction history.

## Depends on
- Step 01 — Database setup (expenses table must exist)
- Step 02 — Registration (user accounts)
- Step 03 — Login and Logout (session + `login_required` decorator)
- Step 07 — Add Expense (expenses exist to delete)
- Step 08 — Edit Expense (`get_expense` helper already in `db.py`; history.html already has an Edit link pattern to follow)

## Routes
- `GET /expenses/<int:id>/delete` — render a confirmation page showing the expense details — logged-in
- `POST /expenses/<int:id>/delete` — delete the expense and redirect to `/profile/history` — logged-in

## Database changes
No new tables or columns. One new helper added to `database/db.py`:
- `delete_expense(expense_id, user_id)` — deletes the row only if it belongs to the given user (enforced by `WHERE id = ? AND user_id = ?`)

`get_expense(expense_id, user_id)` already exists from Step 08 and is reused here to fetch the expense for the confirmation page.

## Templates
- **Create:** `expense-tracker/templates/delete_expense.html` — confirmation page that displays the expense's amount, date, and description, with a "Confirm Delete" POST form and a "Cancel" link back to `/profile/history`; extends `base.html`
- **Modify:** `expense-tracker/templates/history.html` — add a Delete link/button beside the existing Edit link on each expense row, pointing to `url_for('delete_expense', id=expense.id)`

## Files to change
- `expense-tracker/app.py` — replace the stub `delete_expense` route with a GET/POST handler; add `@login_required`; use `abort(404)` if the expense is not found or not owned by the current user; after successful delete flash a success message and redirect to `url_for('transaction_history')`
- `expense-tracker/database/db.py` — add `delete_expense(expense_id, user_id)` helper
- `expense-tracker/templates/history.html` — add Delete link per row beside the Edit link

## Files to create
- `expense-tracker/templates/delete_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with werkzeug (must not be broken)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic lives in `database/db.py` only — no inline SQL in route functions
- Ownership check is mandatory: fetch expense with both `id` and `user_id` using `get_expense`; call `abort(404)` if the result is `None`
- The delete action must use POST — the GET route only renders the confirmation page
- The confirmation page must show enough expense detail (amount, date, description) for the user to verify before confirming
- On successful delete, flash a success message and redirect to `url_for('transaction_history')`
- The "Cancel" link on the confirmation page must return to `url_for('transaction_history')` without making any changes

## Definition of done
- [ ] Visiting `/expenses/1/delete` while logged out redirects to `/login` with a flash message
- [ ] Visiting `/expenses/1/delete` while logged in as the owner renders a confirmation page showing the expense's amount, date, and description
- [ ] Visiting `/expenses/1/delete` while logged in as a different user returns a 404
- [ ] The confirmation page has a "Confirm Delete" button that submits a POST form to `/expenses/1/delete`
- [ ] The confirmation page has a "Cancel" link that navigates back to `/profile/history` without deleting anything
- [ ] Submitting the POST form deletes the expense row from the database and redirects to `/profile/history`
- [ ] A flash success message ("Expense deleted.") is shown after a successful delete
- [ ] The deleted expense no longer appears in the transaction history after deletion
- [ ] The profile stats (count and total) decrease by the correct values after deleting an expense
- [ ] The Delete link is visible on each row in `/profile/history` and navigates to the correct confirmation page
