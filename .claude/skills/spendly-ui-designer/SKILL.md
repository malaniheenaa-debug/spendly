---
name: spendly-ui-designer
description: Generates modern, production-ready UI components and pages for the Spendly expense-tracker app. Use this skill whenever the user asks to design, build, create, redesign, improve, refresh, rework, polish, or fix the look of any page, screen, view, modal, component, card, form, dashboard, table, list, chart, button, navbar, or visual element for Spendly. Trigger on phrases like "Design the ... page", "design a modal for ...", "create UI for ...", "create a component for ...", "build components for ...", "build the ... page", "redesign the ... page", "improve the ... page", "make the ... page better", "polish the dashboard", "rework the profile", "the X page looks ugly", "add a chart card", or any other request that involves producing, modifying, or improving HTML/CSS/Jinja in this app. Trigger even when the user doesn't explicitly say "Spendly" — if they're talking about a page, screen, or component in this project, this skill applies. Lean toward triggering rather than skipping — UI work in this repo should always go through this skill so the output matches the existing design system.
---

# Spendly UI Designer

You design and ship production-quality pages and components for the Spendly Flask app. The goal is output that looks like it was made by the same designer who built the existing landing, login, and profile pages — not a foreign-looking page bolted on top.

## What you're producing

A complete, working contribution to the app — not a sketch. That means:

- A Jinja template in `templates/<name>.html` that extends `base.html`
- CSS rules appended to `static/css/style.css` (or a new `static/css/<page>.css` referenced via `{% block head %}` if the page is large and self-contained, like the landing page is)
- Any small JS in `static/js/` if the page genuinely needs interactivity beyond what CSS handles
- A Flask route added or updated in `app.py` if the page doesn't have one yet

You are not just drafting HTML in a code block — you write the files, wire them up, and the user should be able to run `python app.py` and visit the new page immediately.

## Project conventions you must follow

These exist already and are the source of truth. Do not invent parallel patterns.

### Template structure

Every page extends `base.html` and fills these blocks:

```jinja
{% extends "base.html" %}

{% block title %}Page Name · Spendly{% endblock %}

{% block head %}
  {# optional: page-specific CSS link #}
{% endblock %}

{% block content %}
  <!-- page markup -->
{% endblock %}

{% block scripts %}
  {# optional: page-specific JS #}
{% endblock %}
```

`base.html` already provides the navbar, footer, dark/light toggle, flash messages, and global CSS link. Don't duplicate any of that.

### Color system — use the variables, never hardcode

`style.css` exposes a full design-token system. Always reference these, never paste raw hex values:

| Purpose | Variable |
|---|---|
| Primary text | `--ink` |
| Secondary text | `--ink-soft` |
| Muted/label text | `--ink-muted` |
| Placeholder text | `--ink-faint` |
| Page background | `--paper` |
| Warm section background | `--paper-warm` |
| Card background | `--paper-card` |
| Primary accent (green) | `--accent`, `--accent-light` |
| Secondary accent (orange) | `--accent-2`, `--accent-2-light` |
| Danger (red) | `--danger`, `--danger-light` |
| Borders | `--border`, `--border-soft` |

Using the variables is what makes dark mode work automatically. If you hardcode `#fff` or `#000`, dark mode breaks.

### Typography

- Headlines and large display text: `font-family: var(--font-display)` (DM Serif Display)
- Everything else: DM Sans is inherited from `body`, no need to set
- Fluid sizing for headings: `font-size: clamp(min, vw-based, max)` — e.g. `clamp(1.75rem, 4vw, 2.75rem)`

### Spacing and radii

| Token | Value | Use for |
|---|---|---|
| `--radius-sm` | 6px | buttons, inputs, small chips |
| `--radius-md` | 12px | cards, panels, modals |
| `--radius-lg` | 20px | hero visuals, big feature blocks |
| `--max-width` | 1200px | content container |

Prefer `rem` over `px` for padding, gap, and margin. Standard rhythm is `0.5rem / 0.75rem / 1rem / 1.5rem / 2rem / 3rem`.

### Naming — BEM-inspired, not strict

Block-element-modifier flavored selectors, semantic class names, no utility classes:

- Block: `.expense-card`, `.dashboard-grid`
- Element: `.expense-card__header`, or pragmatically `.expense-header` if it reads cleanly
- Modifier: `.btn-primary`, `.btn-ghost`, `.expense-card--highlight`
- Page-scoped prefix when styles only apply to one page: `.dash-*`, `.exp-*` (mirrors `.lp-*` on the landing page)

### Dark mode

Every component must work in both themes. Two rules:

1. Use color variables everywhere.
2. If a specific element needs a different treatment in dark mode, add a `[data-theme="dark"] .your-selector { ... }` block right under the light-mode rule — don't put dark rules in a separate file.

Test mentally: imagine the page with `--paper` swapped to `#1a1815`. Does anything become unreadable? Fix it before declaring done.

### Responsive

Mobile-first padding (collapses 2rem → 1rem on small screens). Breakpoints in the codebase:

```css
@media (max-width: 900px) { /* tablet — usually drop multi-col grids to 1 col */ }
@media (max-width: 600px) { /* phone — tighten padding, shrink type */ }
```

Use CSS grid with `repeat(auto-fit, minmax(280px, 1fr))` for card grids — it naturally collapses without a media query.

### Buttons

Reuse the existing button classes:
- `.btn-primary` — solid, primary action
- `.btn-ghost` — outlined, secondary action
- `.btn-submit` — full-width form submit
- For destructive: add `.btn-danger` if it doesn't exist yet, using `--danger`

### Forms

Reuse `.form-group`, `.form-label`, `.form-input` from auth pages. Errors render via the global flash system — don't invent a new one.

## How to approach a design request

When the user says something like "Design the expenses page":

### Step 1 — Understand the page's job

Before opening any file, decide:
- What's the **primary action** a user takes here? (e.g. on a dashboard: scan totals; on expenses: add/find a transaction)
- What are the **secondary actions**? (filter, edit, delete)
- What **data** does the page need? — check `app.py` and the SQLite schema (`database/db.py`)
- What **state** does it have? — empty state, populated state, loading, error

Empty states are not optional. Every list/table needs a designed empty state.

### Step 2 — Sketch the layout in words first

Briefly tell the user the structure you're going to build, in 4–6 lines. Example:

> Dashboard layout:
> - Top: greeting + month selector
> - Row of 3 summary cards (total spent, top category, expense count)
> - Two-column section: recent expenses list (left, 60%) + category breakdown chart (right, 40%)
> - Floating "Add expense" button bottom-right on mobile

This gives the user a chance to redirect before you write 200 lines of CSS.

### Step 3 — Check the route and context

Read `app.py`. If the route exists as a stub, fill it in with a real `render_template` call and the context variables the template needs. If it doesn't exist, add it. If it requires login, decorate it with `@login_required`.

Read `database/db.py` to make sure any queries you plan match the actual schema.

### Step 4 — Write the template

Write the full Jinja template in `templates/`. Use semantic HTML (`<header>`, `<section>`, `<article>`, `<nav>`) over divs where it improves clarity. Add `aria-label` on icon-only buttons.

### Step 5 — Write the CSS

Append to `static/css/style.css` under a clearly-commented section:

```css
/* ====================================================== */
/* Expenses page                                          */
/* ====================================================== */
```

Group rules logically (layout → cards → list items → empty state → responsive overrides → dark mode overrides).

### Step 6 — JS only if needed

Most pages need no JS. If you need a confirm dialog, filter dropdown, or modal toggle, write a small IIFE in `static/js/<page>.js` and load it via `{% block scripts %}`. Match the style of `static/js/main.js` — pure DOM, no dependencies.

### Step 7 — Show what you did

After saving the files, summarise:
- Files created/changed (as clickable links)
- The route to visit (e.g. `http://localhost:5001/expenses`)
- One line on the visual approach you took
- Any DB queries the page needs that aren't implemented yet, so the user knows what's mocked vs real

## Design defaults — what "modern and production-ready" means here

Spendly's existing pages have a specific aesthetic: warm off-white paper background, serif display headings, generous whitespace, subtle borders, no shadows-as-decoration, restrained accent colors. Stay in that lane unless the user asks for something different.

Concretely:

- **Cards** sit on `--paper-card` with `1px solid var(--border)` and `--radius-md`. No drop shadows by default; use border + slight background tint for separation.
- **Numbers and money** use the display serif for emphasis on big totals (e.g. `₹12,450` on a dashboard card), DM Sans elsewhere.
- **Tables** — prefer styled lists of cards over true `<table>` markup for expense feeds. Use real `<table>` only for dense data.
- **Density** — moderate. Not Notion-airy, not GitHub-dense. Padding inside cards should be `1.25rem` to `1.75rem`.
- **Motion** — sparing. `transition: 0.15s ease` on hover states. No bouncy animations.
- **Icons** — use Unicode symbols (◈, ›, ✕, ↗) as the codebase already does, or inline SVGs. Don't add an icon-font dependency.
- **Currency** — Spendly is INR-flavored based on the seed data. Use `₹` and Indian number formatting (`12,450` not `12450`).
- **Charts** — if you need a simple bar/pie, build it in pure CSS or inline SVG. Don't add Chart.js unless the page genuinely needs interactive charts.

## Examples of how to interpret requests

**"Design the expenses list page"**
→ Full page with: month/category filter row, scrollable list of expense cards (date · category badge · description · amount), empty state when no expenses, "Add expense" CTA in the top-right, responsive collapse to single column.

**"Design a modal for adding an expense"**
→ Inline modal (no library), backdrop click to dismiss, form with date, category dropdown, amount, description, submit + cancel. Trapped focus and ESC to close. CSS-only show/hide toggled by a small JS function.

**"Design the dashboard"**
→ Greeting, month picker, 3-card summary row, recent-expenses preview list, category-spend breakdown as a CSS bar chart. Empty state if user has zero expenses prompts them to add their first.

**"Design a settings page"**
→ Stacked card sections: Profile (name, email — readonly with edit button), Password (change form), Categories (list with add/remove), Danger zone (delete account, red).

## Things to avoid

- Don't pull in Tailwind, Bootstrap, or any CSS framework. The project deliberately uses hand-written CSS with variables.
- Don't add JS frameworks (React, Vue, Alpine). Plain JS only.
- Don't hardcode colors — always variables.
- Don't add new fonts. DM Sans + DM Serif Display are the whole type system.
- Don't introduce drop shadows as the primary separation mechanism (the design uses borders).
- Don't write inline styles in the template (`style="..."`) — put it in CSS.
- Don't forget the dark-mode pass. If you don't verify dark mode, the page is half-done.
- Don't skip the empty state on any list or grid.

## When the user is vague

If the request is just "design the X page" with no further detail, do not pepper them with questions. Make sensible product decisions, state them briefly ("I'll show monthly totals + recent expenses + category breakdown"), then build. The user can redirect after seeing it. Speed beats certainty here — they can iterate.

Only ask a question if there's a genuinely ambiguous choice that would force a rewrite (e.g. "should the dashboard show all-time or current-month by default?"). And even then, propose your pick and ask for a yes/no.
