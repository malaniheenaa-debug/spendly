---
name: project-test-conventions
description: Established pytest conventions for the Spendly test suite — fixture patterns, in-memory DB strategy, session injection, and file locations.
metadata:
  type: project
---

**Test file location:** `expense-tracker/expense-tracker/tests/test_<feature>.py`  
An `__init__.py` is required in `tests/` for module discovery.

**In-memory database pattern**
- Monkey-patch `database.db.get_db` inside the `app` fixture to redirect all DB calls to a single `sqlite3.connect(":memory:")` connection.
- Wrap the connection in a `_NonClosingProxy` class so that route-level `conn.close()` calls do not destroy the shared in-memory DB mid-test.
- Restore the original `get_db` and close the real connection in fixture teardown.
- Schema is bootstrapped manually inside the fixture using `executescript`; do not call `init_db()` (it would hit the real DB before the patch is in place).

**Session injection (login bypass)**
- Use `with client.session_transaction() as sess: sess["user_id"] = ...; sess["user_name"] = ...` rather than a real POST /login round-trip.
- This keeps auth tests orthogonal from feature tests.

**Fixture hierarchy**
- `app` — patched Flask app, yields, tears down.
- `db_conn` — thin proxy to the in-memory connection for direct data setup.
- `seeded_client` — authenticated client + known expenses (dates: 2024-01-15, 2024-02-20, 2024-03-10; amounts: 100, 200, 300 for Food/Travel/Bills).
- `empty_client` — authenticated client with zero expenses.
- `unauthenticated_client` — no session.

**HTML assertion pattern**
- Decode via `response.data.decode("utf-8")`.
- Assert on visible text strings (headings, flash messages, expense descriptions).
- Assert on `value="YYYY-MM-DD"` for pre-populated date inputs.
- Assert on CSS class names (e.g., `filter-clear`) for presence/absence of UI controls.

**Named date/amount constants**
- Always use named constants (`DATE_JAN`, `AMOUNT_FEB`, etc.) — never magic strings.

**Why:** Established during Step 06 date filter test generation. Captures non-obvious choices (proxy class, session injection, constant naming) for future consistency.
**How to apply:** Follow these patterns verbatim when generating tests for any future Spendly step so fixtures are reusable across test files. See [[project-spendly-domain]] for domain facts.
