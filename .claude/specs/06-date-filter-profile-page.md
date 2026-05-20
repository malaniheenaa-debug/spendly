# Spec: Date Filter for Profile Page

## Overview

Add an optional date-range filter to the three profile sub-pages — Transaction History, Summary Stats, and Category Breakdown. Users can enter a "from" and "to" date, submit the form, and see only the expenses that fall within that window. Both dates are optional; omitting them shows all data (no change from current behaviour). The filter is driven entirely by GET query parameters so filtered URLs are bookmarkable and shareable.

## Depends on

- Step 1: Database setup (`expenses.date DATE` column must exist)
- Step 3: Login and Logout (`login_required` decorator, `session["user_id"]`)
- Step 5: Backend Routes for Profile Page (`/profile/history`, `/profile/stats`, `/profile/categories` must be live)

## Routes

All three existing sub-routes gain optional query-param support — no new routes are added.

| Method | Path | Change |
|--------|------|--------|
| `GET` | `/profile/history` | Accept `?from=YYYY-MM-DD&to=YYYY-MM-DD`; filter returned rows |
| `GET` | `/profile/stats` | Accept `?from=YYYY-MM-DD&to=YYYY-MM-DD`; show filtered-period stats when active |
| `GET` | `/profile/categories` | Accept `?from=YYYY-MM-DD&to=YYYY-MM-DD`; filter expenses in category totals |

## Database changes

No database changes. The `expenses.date` column (`DATE NOT NULL`) already exists and is used as the filter key.

## Templates

- **Modify:** `expense-tracker/templates/history.html`
  - Add a date-filter form above the table card
  - Show result count and active date range when a filter is applied
- **Modify:** `expense-tracker/templates/stats.html`
  - Add a date-filter form above the stat sections
  - When filter is active: replace "This Month" / "All Time" sections with a single "Filtered Period" section
  - When no filter: keep current "This Month" + "All Time" layout
- **Modify:** `expense-tracker/templates/categories.html`
  - Add a date-filter form above the category list
  - Show active date range label when filter is applied

## Files to change

- `expense-tracker/app.py`
  - `transaction_history()` — read `from` / `to` query params, build conditional SQL, pass `from_date` / `to_date` back to template
  - `summary_stats()` — read `from` / `to` query params; when active run a single filtered-period query instead of the separate `this_month` / `all_time` queries
  - `category_breakdown()` — read `from` / `to` query params, add date conditions to the JOIN filter and grand total query
- `expense-tracker/templates/history.html` — add filter form + active-filter label
- `expense-tracker/templates/stats.html` — add filter form + conditional section rendering
- `expense-tracker/templates/categories.html` — add filter form + active-filter label

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — never interpolate `from_date` / `to_date` into SQL strings
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Both `from` and `to` are optional; when absent the query must behave identically to the current implementation (no performance regression, same results)
- Validate date format in Python before using in SQL — if a param is present but not a valid `YYYY-MM-DD` string, flash an error and redirect back without applying the filter
- The filter form must be a `GET` form so the query params appear in the URL
- Persist the current filter values back into the form inputs so the user can see what they filtered by and refine it

## Implementation detail

### Query-param parsing helper (add once in `app.py`, above the sub-routes)

```python
import re

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def _parse_date_params():
    """Return (from_date, to_date) strings or None; flash + return (None, None) on bad input."""
    from_date = request.args.get("from", "").strip() or None
    to_date   = request.args.get("to",   "").strip() or None
    for val in (from_date, to_date):
        if val and not _DATE_RE.match(val):
            flash("Invalid date format — use YYYY-MM-DD.", "error")
            return None, None
    return from_date, to_date
```

### `transaction_history()` — updated query

```python
@app.route("/profile/history")
@login_required
def transaction_history():
    from_date, to_date = _parse_date_params()
    conn = get_db()
    try:
        expenses = conn.execute(
            """
            SELECT e.id, e.amount, e.date, e.description,
                   COALESCE(c.name, 'Uncategorised') AS category
            FROM expenses e
            LEFT JOIN categories c ON c.id = e.category_id
            WHERE e.user_id = ?
              AND (? IS NULL OR e.date >= ?)
              AND (? IS NULL OR e.date <= ?)
            ORDER BY e.date DESC, e.id DESC
            """,
            (session["user_id"], from_date, from_date, to_date, to_date)
        ).fetchall()
    finally:
        conn.close()
    return render_template(
        "history.html",
        expenses=expenses,
        user_name=session["user_name"],
        from_date=from_date,
        to_date=to_date,
    )
```

### `summary_stats()` — updated query

```python
@app.route("/profile/stats")
@login_required
def summary_stats():
    from_date, to_date = _parse_date_params()
    conn = get_db()
    try:
        if from_date or to_date:
            filtered = conn.execute(
                """
                SELECT COUNT(*) AS count,
                       COALESCE(SUM(amount), 0) AS total,
                       COALESCE(AVG(amount), 0) AS avg,
                       COALESCE(MAX(amount), 0) AS biggest
                FROM expenses
                WHERE user_id = ?
                  AND (? IS NULL OR date >= ?)
                  AND (? IS NULL OR date <= ?)
                """,
                (session["user_id"], from_date, from_date, to_date, to_date)
            ).fetchone()
            all_time   = None
            this_month = None
        else:
            filtered = None
            all_time = conn.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total, COALESCE(AVG(amount), 0) AS avg, COALESCE(MAX(amount), 0) AS biggest FROM expenses WHERE user_id = ?",
                (session["user_id"],)
            ).fetchone()
            this_month = conn.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')",
                (session["user_id"],)
            ).fetchone()
    finally:
        conn.close()
    return render_template(
        "stats.html",
        all_time=all_time,
        this_month=this_month,
        filtered=filtered,
        user_name=session["user_name"],
        from_date=from_date,
        to_date=to_date,
    )
```

### `category_breakdown()` — updated query

```python
@app.route("/profile/categories")
@login_required
def category_breakdown():
    from_date, to_date = _parse_date_params()
    conn = get_db()
    try:
        categories = conn.execute(
            """
            SELECT c.name,
                   COUNT(e.id)                AS count,
                   COALESCE(SUM(e.amount), 0) AS total
            FROM categories c
            LEFT JOIN expenses e
                   ON e.category_id = c.id
                  AND e.user_id = ?
                  AND (? IS NULL OR e.date >= ?)
                  AND (? IS NULL OR e.date <= ?)
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY total DESC
            """,
            (session["user_id"], from_date, from_date, to_date, to_date, session["user_id"])
        ).fetchall()
        grand_total = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = ?
              AND (? IS NULL OR date >= ?)
              AND (? IS NULL OR date <= ?)
            """,
            (session["user_id"], from_date, from_date, to_date, to_date)
        ).fetchone()
    finally:
        conn.close()
    return render_template(
        "categories.html",
        categories=categories,
        grand_total=grand_total["total"],
        user_name=session["user_name"],
        from_date=from_date,
        to_date=to_date,
    )
```

### Filter form snippet (add to each template, above the main card/section)

```html
<form class="date-filter-form" method="get" action="">
  <div class="filter-fields">
    <label class="filter-label">
      From
      <input class="filter-input" type="date" name="from"
             value="{{ from_date or '' }}">
    </label>
    <label class="filter-label">
      To
      <input class="filter-input" type="date" name="to"
             value="{{ to_date or '' }}">
    </label>
  </div>
  <div class="filter-actions">
    <button class="filter-btn" type="submit">Filter</button>
    {% if from_date or to_date %}
    <a class="filter-clear" href="{{ request.path }}">Clear</a>
    {% endif %}
  </div>
</form>

{% if from_date or to_date %}
<p class="filter-active-label">
  Showing results
  {% if from_date %} from <strong>{{ from_date }}</strong>{% endif %}
  {% if to_date %} to <strong>{{ to_date }}</strong>{% endif %}
</p>
{% endif %}
```

### CSS to add (inline `<style>` in each template's `{% block head %}`)

Use only existing CSS variables:

```css
.date-filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  padding: 1rem 1.25rem;
  background: var(--paper-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.filter-fields {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex: 1;
}

.filter-label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-muted);
}

.filter-input {
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--paper);
  color: var(--ink);
  font-size: 0.9rem;
  font-family: var(--font-body);
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filter-btn {
  padding: 0.5rem 1.1rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.filter-btn:hover { opacity: 0.85; }

.filter-clear {
  font-size: 0.875rem;
  color: var(--ink-muted);
  text-decoration: none;
  transition: color 0.15s;
}

.filter-clear:hover { color: var(--ink); }

.filter-active-label {
  font-size: 0.85rem;
  color: var(--ink-muted);
  margin-bottom: 1rem;
}
```

## Definition of done

- [ ] Visit `/profile/history` with no query params → all expenses shown, no filter UI is pre-filled
- [ ] Submit the filter form with a `from` date only → only expenses on or after that date are shown
- [ ] Submit the filter form with a `to` date only → only expenses on or before that date are shown
- [ ] Submit with both `from` and `to` → only expenses in that inclusive range are shown
- [ ] The filter form inputs are pre-populated with the active `from` / `to` values after filtering
- [ ] A "Clear" link appears when a filter is active and resets to the unfiltered view
- [ ] An active-filter label is visible below the form when a filter is applied (e.g. "Showing results from 2026-05-01 to 2026-05-31")
- [ ] `/profile/stats` with a date filter shows a single "Filtered Period" section (count, total, avg, biggest) instead of "This Month" / "All Time"
- [ ] `/profile/stats` with no date filter still shows the original "This Month" + "All Time" layout
- [ ] `/profile/categories` with a date filter shows category totals for only that date range
- [ ] An expense outside the date range is excluded from all three pages when the filter covers a window that doesn't include it
- [ ] Passing a malformed date (e.g. `?from=not-a-date`) flashes an error and returns unfiltered results
- [ ] Filter form renders correctly in both light and dark mode (no hardcoded colours)
- [ ] All three pages pass the `login_required` check (no regression)
