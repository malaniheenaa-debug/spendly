# Spec: Profile Page Design

## Overview

Implement the user profile page, replacing the current stub that returns a plain string for `GET /profile`. The page displays the logged-in user's name, email, and account creation date alongside a brief expense summary (total expenses count and total amount spent). This is the first "interior" page of Spendly — it establishes the authenticated layout pattern that later expense pages (Steps 7–9) will follow.

## Depends on

- Step 1: Database setup (`database/db.py` — `get_db()`, `users` and `expenses` tables)
- Step 2: Registration (user rows exist in `users`)
- Step 3: Login and Logout (`login_required` decorator, `session["user_id"]`, `session["user_name"]`)

## Routes

- `GET /profile` — renders the profile page with user info and expense summary — logged-in only

No new routes. The existing stub route in `app.py` is replaced with a real implementation.

## Database changes

No database changes. All required columns already exist:
- `users`: `id`, `name`, `email`, `created_at`
- `expenses`: `id`, `user_id`, `amount`

## Templates

- **Create:** `expense-tracker/templates/profile.html` — profile page with user info card and expense stats
- **Modify:** none

## Files to change

- `expense-tracker/app.py` — replace the stub `/profile` route body with a real DB query and `render_template` call

## Files to create

- `expense-tracker/templates/profile.html`
- `expense-tracker/static/css/profile.css`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (no changes to passwords here, rule included for completeness)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `@login_required` must remain on the `/profile` route
- Close the DB connection in a `finally` block or use `with`

## Route implementation detail

Replace the stub in `app.py`:

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

## Template structure (`profile.html`)

```
{% extends "base.html" %}
{% block title %}Profile — Spendly{% endblock %}
{% block head %}<link rel="stylesheet" href="{{ url_for('static', filename='css/profile.css') }}">{% endblock %}

{% block content %}
<div class="profile-container">

  <div class="profile-card">
    <div class="profile-avatar">{{ user['name'][0].upper() }}</div>
    <h1 class="profile-name">{{ user['name'] }}</h1>
    <p class="profile-email">{{ user['email'] }}</p>
    <p class="profile-since">Member since {{ user['created_at'][:10] }}</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <span class="stat-value">{{ stats['count'] }}</span>
      <span class="stat-label">Expenses</span>
    </div>
    <div class="stat-card">
      <span class="stat-value">₹{{ "%.2f"|format(stats['total']) }}</span>
      <span class="stat-label">Total Spent</span>
    </div>
  </div>

</div>
{% endblock %}
```

## CSS notes (`profile.css`)

Use only variables from `style.css` `:root`:
- `--paper-card`, `--border`, `--radius-md`, `--radius-lg`
- `--ink`, `--ink-soft`, `--ink-muted`
- `--accent`, `--accent-light`
- `--font-display`, `--font-body`

Key layout classes needed:
- `.profile-container` — centred column, max-width ~480px, padding top
- `.profile-card` — card background `--paper-card`, border `--border`, rounded `--radius-lg`, text-centred
- `.profile-avatar` — large circle, `--accent` background, white initial letter, `--font-display`
- `.profile-name` — `--font-display`, large
- `.profile-email`, `.profile-since` — `--ink-muted`, small
- `.stats-grid` — two-column grid
- `.stat-card` — card background, centred, `--accent-light` background
- `.stat-value` — large number, `--accent` colour, `--font-display`
- `.stat-label` — `--ink-muted`, uppercase, small

## Definition of done

- [ ] Visit `/profile` without being logged in → redirected to `/login` with flash "Please sign in to continue."
- [ ] Log in and visit `/profile` → page renders with no errors and no stub string
- [ ] Profile card shows the logged-in user's name, email, and a "Member since" date
- [ ] Stats grid shows correct expense count and total (verify against DB or seed data)
- [ ] Avatar circle shows the first letter of the user's name, uppercased
- [ ] Page renders correctly in both light and dark mode (no hardcoded colours visible)
- [ ] Navbar still shows user's name and "Sign out" link (inherited from `base.html`)
- [ ] A user with zero expenses sees count `0` and total `₹0.00` (no crash)
