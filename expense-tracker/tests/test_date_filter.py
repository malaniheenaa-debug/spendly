"""
tests/test_date_filter.py

Behavior tests for Step 06: Date Filter for Profile Page.

Covers GET query params ?from=YYYY-MM-DD and ?to=YYYY-MM-DD on:
  - /profile/history
  - /profile/stats
  - /profile/categories

Test strategy
-------------
* Every test uses a fresh in-memory SQLite database — the real spendly.db
  is never touched.
* A logged-in session is established by injecting the session dict directly;
  no real HTTP login round-trip is needed.
* Expenses with known, spread-out dates are seeded once per class so that
  date-range assertions are deterministic.
* All assertions are against HTTP status codes and rendered HTML text —
  never against internal variables or query construction.

Run with:
    pytest tests/test_date_filter.py -v
"""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash

# ---------------------------------------------------------------------------
# App factory — isolate every test run with a fresh :memory: database
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """
    Create a fresh Flask application instance backed by an in-memory SQLite
    database.  The module-level ``app`` object in app.py hard-codes a
    DATABASE path, so we monkey-patch ``database.db.get_db`` to redirect all
    connections to the shared in-memory connection for the duration of the
    test.
    """
    import database.db as db_module
    import app as app_module

    # One shared in-memory connection (same URI = same database).
    mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
    mem_conn.row_factory = sqlite3.Row
    mem_conn.execute("PRAGMA foreign_keys = ON")

    # Bootstrap the schema using the real executescript from db.py.
    mem_conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name       TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            amount      REAL    NOT NULL,
            date        DATE    NOT NULL,
            description TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    mem_conn.commit()

    original_db_get_db  = db_module.get_db
    original_app_get_db = app_module.get_db

    def patched_get_db():
        # Return a thin wrapper: same underlying connection, but calling
        # .close() on it must NOT close the shared connection (tests share it).
        class _NonClosingProxy:
            def __init__(self, conn):
                self._conn = conn

            def execute(self, *a, **kw):
                return self._conn.execute(*a, **kw)

            def executemany(self, *a, **kw):
                return self._conn.executemany(*a, **kw)

            def executescript(self, *a, **kw):
                return self._conn.executescript(*a, **kw)

            def commit(self):
                return self._conn.commit()

            def close(self):
                pass  # intentional no-op — we own the lifetime

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

        return _NonClosingProxy(mem_conn)

    # Patch both the source module and the name already imported into app.py.
    # app.py uses `from database.db import get_db`, so patching only db_module
    # does not affect the name bound in app.py's own namespace.
    db_module.get_db  = patched_get_db
    app_module.get_db = patched_get_db

    flask_app = app_module.app
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app

    # Restore both references and close the in-memory connection.
    db_module.get_db  = original_db_get_db
    app_module.get_db = original_app_get_db
    mem_conn.close()


# ---------------------------------------------------------------------------
# Reusable helpers
# ---------------------------------------------------------------------------

USER_NAME  = "Alice"
USER_EMAIL = "alice@example.com"
USER_PASS  = "s3cret!!"

# Anchored expense dates — deliberately placed in the past so they never
# collide with the SQLite "this month" window in an unpredictable way.
DATE_JAN = "2024-01-15"
DATE_FEB = "2024-02-20"
DATE_MAR = "2024-03-10"

AMOUNT_JAN = 100.00   # Food
AMOUNT_FEB = 200.00   # Travel
AMOUNT_MAR = 300.00   # Bills


@pytest.fixture()
def db_conn(app):
    """Expose the in-memory connection for direct data setup in tests."""
    import database.db as db_module
    # Call patched get_db to get the proxy, then reach through to raw conn.
    proxy = db_module.get_db()
    return proxy


@pytest.fixture()
def seeded_client(app, db_conn):
    """
    HTTP test client with:
      * One registered user (Alice).
      * Three categories: Food, Travel, Bills.
      * Three expenses on DATE_JAN, DATE_FEB, DATE_MAR respectively.
      * An active server-side session for Alice.
    """
    # Insert user.
    cur = db_conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (USER_NAME, USER_EMAIL, generate_password_hash(USER_PASS)),
    )
    db_conn.commit()
    user_id = cur.lastrowid

    # Insert categories.
    db_conn.executemany(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        [(user_id, "Food"), (user_id, "Travel"), (user_id, "Bills")],
    )
    db_conn.commit()

    food_id   = db_conn.execute(
        "SELECT id FROM categories WHERE user_id=? AND name='Food'", (user_id,)
    ).execute if False else db_conn.execute(
        "SELECT id FROM categories WHERE user_id=? AND name='Food'", (user_id,)
    ).fetchone()["id"]

    travel_id = db_conn.execute(
        "SELECT id FROM categories WHERE user_id=? AND name='Travel'", (user_id,)
    ).fetchone()["id"]

    bills_id  = db_conn.execute(
        "SELECT id FROM categories WHERE user_id=? AND name='Bills'", (user_id,)
    ).fetchone()["id"]

    # Insert expenses.
    db_conn.executemany(
        "INSERT INTO expenses (user_id, category_id, amount, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, food_id,   AMOUNT_JAN, DATE_JAN, "January groceries"),
            (user_id, travel_id, AMOUNT_FEB, DATE_FEB, "February flight"),
            (user_id, bills_id,  AMOUNT_MAR, DATE_MAR, "March electricity"),
        ],
    )
    db_conn.commit()

    # Build an authenticated test client.
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"]   = user_id
        sess["user_name"] = USER_NAME

    # Expose user_id to tests via attribute for convenience.
    client._test_user_id = user_id
    return client


@pytest.fixture()
def empty_client(app, db_conn):
    """
    Authenticated test client with a registered user but NO expenses.
    Used for zero-state assertions.
    """
    cur = db_conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        ("Bob", "bob@example.com", generate_password_hash("password1")),
    )
    db_conn.commit()
    user_id = cur.lastrowid

    db_conn.executemany(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        [(user_id, cat) for cat in ["Food", "Travel", "Bills", "Entertainment"]],
    )
    db_conn.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"]   = user_id
        sess["user_name"] = "Bob"
    return client


@pytest.fixture()
def unauthenticated_client(app):
    """Test client with no active session — anonymous user."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _html(response) -> str:
    """Decode response data to a plain string for assertion readability."""
    return response.data.decode("utf-8")


# ===========================================================================
# 1. Authentication guard — all three routes require login
# ===========================================================================

class TestAuthenticationRequired:
    """All three profile sub-routes must redirect unauthenticated requests."""

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_unauthenticated_request_redirects_to_login(
        self, unauthenticated_client, path
    ):
        """
        Verify that an anonymous GET to any date-filter route results in a
        redirect to /login, not a 200 or a server error.
        """
        response = unauthenticated_client.get(path)

        assert response.status_code in (301, 302), (
            f"Expected a redirect for unauthenticated request to {path}, "
            f"got {response.status_code}"
        )
        assert "/login" in response.headers["Location"]

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_unauthenticated_request_with_date_params_still_redirects(
        self, unauthenticated_client, path
    ):
        """
        Date params must not bypass the login requirement.
        """
        response = unauthenticated_client.get(
            f"{path}?from=2024-01-01&to=2024-12-31"
        )

        assert response.status_code in (301, 302)
        assert "/login" in response.headers["Location"]


# ===========================================================================
# 2. /profile/history — date filter behaviour
# ===========================================================================

class TestHistoryDateFilter:
    """Behaviour tests for GET /profile/history with ?from and ?to params."""

    def test_no_params_returns_all_expenses(self, seeded_client):
        """
        Calling /profile/history with no query params must show every expense
        for the logged-in user regardless of date.
        """
        response = seeded_client.get("/profile/history")

        assert response.status_code == 200
        body = _html(response)
        assert "January groceries" in body
        assert "February flight"   in body
        assert "March electricity" in body

    def test_from_param_excludes_earlier_expenses(self, seeded_client):
        """
        ?from=DATE must exclude expenses strictly before that date.
        The January expense must not appear when from=2024-02-01.
        """
        response = seeded_client.get("/profile/history?from=2024-02-01")

        assert response.status_code == 200
        body = _html(response)
        assert "January groceries" not in body
        assert "February flight"   in body
        assert "March electricity" in body

    def test_to_param_excludes_later_expenses(self, seeded_client):
        """
        ?to=DATE must exclude expenses strictly after that date.
        The March expense must not appear when to=2024-02-28.
        """
        response = seeded_client.get("/profile/history?to=2024-02-28")

        assert response.status_code == 200
        body = _html(response)
        assert "January groceries" in body
        assert "February flight"   in body
        assert "March electricity" not in body

    def test_from_and_to_together_return_inclusive_range(self, seeded_client):
        """
        ?from=DATE&to=DATE must return only expenses within the inclusive
        range [from, to].  Expenses outside must be absent.
        """
        response = seeded_client.get(
            f"/profile/history?from={DATE_FEB}&to={DATE_FEB}"
        )

        assert response.status_code == 200
        body = _html(response)
        # Only the exact boundary date should appear.
        assert "February flight"   in body
        assert "January groceries" not in body
        assert "March electricity" not in body

    def test_from_boundary_is_inclusive(self, seeded_client):
        """
        An expense whose date equals the ?from= value must be included.
        """
        response = seeded_client.get(f"/profile/history?from={DATE_JAN}")

        assert response.status_code == 200
        assert "January groceries" in _html(response)

    def test_to_boundary_is_inclusive(self, seeded_client):
        """
        An expense whose date equals the ?to= value must be included.
        """
        response = seeded_client.get(f"/profile/history?to={DATE_MAR}")

        assert response.status_code == 200
        assert "March electricity" in _html(response)

    def test_range_with_no_matching_expenses_shows_empty_state(
        self, seeded_client
    ):
        """
        A date range that matches zero expenses must render the empty-state
        block rather than a table or a server error.
        """
        response = seeded_client.get(
            "/profile/history?from=2030-01-01&to=2030-12-31"
        )

        assert response.status_code == 200
        body = _html(response)
        # None of the seeded descriptions should be present.
        assert "January groceries" not in body
        assert "February flight"   not in body
        assert "March electricity" not in body
        # The empty-state element from history.html should appear.
        assert "No transactions yet" in body

    def test_only_from_param_with_future_range_shows_empty_state(
        self, seeded_client
    ):
        """
        When ?from= is set to a date after all seeded expenses, no expenses
        should be returned and the page must still load without error.
        """
        response = seeded_client.get("/profile/history?from=2099-01-01")

        assert response.status_code == 200
        assert "No transactions yet" in _html(response)


# ===========================================================================
# 3. /profile/history — filter UI elements in rendered HTML
# ===========================================================================

class TestHistoryFilterUI:
    """Verify that filter form controls reflect the active filter state."""

    def test_filter_form_input_prepopulated_with_from_value(
        self, seeded_client
    ):
        """
        When ?from=DATE is active, the rendered HTML must pre-populate the
        'from' date input with that value so the user can see the current filter.
        """
        response = seeded_client.get(f"/profile/history?from={DATE_JAN}")

        assert response.status_code == 200
        body = _html(response)
        assert f'value="{DATE_JAN}"' in body

    def test_filter_form_input_prepopulated_with_to_value(
        self, seeded_client
    ):
        """
        When ?to=DATE is active, the 'to' date input must be pre-populated.
        """
        response = seeded_client.get(f"/profile/history?to={DATE_MAR}")

        assert response.status_code == 200
        body = _html(response)
        assert f'value="{DATE_MAR}"' in body

    def test_clear_link_present_when_from_is_active(self, seeded_client):
        """
        A 'Clear' link must appear in the HTML when a ?from= filter is active,
        giving the user a one-click way to remove the filter.
        """
        response = seeded_client.get(f"/profile/history?from={DATE_JAN}")

        assert response.status_code == 200
        assert "Clear" in _html(response)

    def test_clear_link_present_when_to_is_active(self, seeded_client):
        """
        A 'Clear' link must appear in the HTML when a ?to= filter is active.
        """
        response = seeded_client.get(f"/profile/history?to={DATE_MAR}")

        assert response.status_code == 200
        assert "Clear" in _html(response)

    def test_clear_link_present_when_both_params_active(self, seeded_client):
        """
        A 'Clear' link must appear when both ?from= and ?to= are provided.
        """
        response = seeded_client.get(
            f"/profile/history?from={DATE_JAN}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        assert "Clear" in _html(response)

    def test_clear_link_absent_when_no_filter_active(self, seeded_client):
        """
        When no filter params are present, the 'Clear' link must NOT appear
        so the UI is not cluttered with a non-functional control.
        """
        response = seeded_client.get("/profile/history")

        assert response.status_code == 200
        # Check for the anchor element, not the CSS class name — the class
        # name also appears in the inline <style> block unconditionally.
        assert '<a class="filter-clear"' not in _html(response)

    def test_active_filter_label_present_when_from_is_active(
        self, seeded_client
    ):
        """
        When a date filter is active, the page must display a human-readable
        label indicating that results are filtered (e.g. 'Showing results from …').
        """
        response = seeded_client.get(f"/profile/history?from={DATE_FEB}")

        assert response.status_code == 200
        body = _html(response)
        assert "Showing results" in body
        assert DATE_FEB in body

    def test_active_filter_label_present_when_to_is_active(
        self, seeded_client
    ):
        """
        The active-filter label must also appear when only ?to= is provided.
        """
        response = seeded_client.get(f"/profile/history?to={DATE_MAR}")

        assert response.status_code == 200
        body = _html(response)
        assert "Showing results" in body
        assert DATE_MAR in body

    def test_active_filter_label_absent_when_no_filter_active(
        self, seeded_client
    ):
        """
        When no filter params are set, the 'Showing results' label must NOT
        appear in the unfiltered view.
        """
        response = seeded_client.get("/profile/history")

        assert response.status_code == 200
        assert "Showing results" not in _html(response)


# ===========================================================================
# 4. /profile/stats — date filter behaviour
# ===========================================================================

class TestStatsDateFilter:
    """Behaviour tests for GET /profile/stats with ?from and ?to params."""

    def test_no_params_shows_this_month_section(self, seeded_client):
        """
        Without any date params, the stats page must render the 'This Month'
        section.  'Filtered Period' must NOT appear.
        """
        response = seeded_client.get("/profile/stats")

        assert response.status_code == 200
        body = _html(response)
        assert "This Month"       in body
        assert "Filtered Period"  not in body

    def test_no_params_shows_all_time_section(self, seeded_client):
        """
        Without any date params, the stats page must also render the
        'All Time' section alongside 'This Month'.
        """
        response = seeded_client.get("/profile/stats")

        assert response.status_code == 200
        assert "All Time" in _html(response)

    def test_with_date_params_shows_filtered_period_section(
        self, seeded_client
    ):
        """
        When date params are supplied, the stats page must render a
        'Filtered Period' section showing aggregated stats for that range.
        """
        response = seeded_client.get(
            f"/profile/stats?from={DATE_JAN}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        assert "Filtered Period" in _html(response)

    def test_with_date_params_hides_this_month_section(self, seeded_client):
        """
        When date params are supplied, the 'This Month' section must NOT
        appear — the user has asked for a specific custom range.
        """
        response = seeded_client.get(
            f"/profile/stats?from={DATE_JAN}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        assert "This Month" not in _html(response)

    def test_with_date_params_hides_all_time_section(self, seeded_client):
        """
        When date params are supplied, the 'All Time' section must NOT appear.
        """
        response = seeded_client.get(
            f"/profile/stats?from={DATE_JAN}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        assert "All Time" not in _html(response)

    def test_with_only_from_param_shows_filtered_period(self, seeded_client):
        """
        A lone ?from= param (no ?to=) is enough to trigger the filtered view.
        """
        response = seeded_client.get(f"/profile/stats?from={DATE_FEB}")

        assert response.status_code == 200
        assert "Filtered Period" in _html(response)

    def test_with_only_to_param_shows_filtered_period(self, seeded_client):
        """
        A lone ?to= param (no ?from=) is enough to trigger the filtered view.
        """
        response = seeded_client.get(f"/profile/stats?to={DATE_FEB}")

        assert response.status_code == 200
        assert "Filtered Period" in _html(response)

    def test_filtered_stats_reflect_only_matching_expenses(
        self, seeded_client
    ):
        """
        The rendered 'Filtered Period' aggregate must count only the expenses
        within the supplied date range — not all-time data.

        Seeded: Jan 100, Feb 200, Mar 300.  Range [Jan, Jan] → count=1.
        """
        response = seeded_client.get(
            f"/profile/stats?from={DATE_JAN}&to={DATE_JAN}"
        )

        assert response.status_code == 200
        body = _html(response)
        # Exactly one expense in range: count = 1, total = 100.00.
        assert ">1<"       in body   # stat-value for Expenses
        assert "100.00"    in body   # total / avg / biggest all = 100.00

    def test_zero_matching_expenses_shows_empty_state_without_crash(
        self, seeded_client
    ):
        """
        When the date range matches zero expenses, the page must return 200
        and display an 'empty' message — not raise a server error or divide
        by zero.
        """
        response = seeded_client.get(
            "/profile/stats?from=2030-01-01&to=2030-12-31"
        )

        assert response.status_code == 200
        body = _html(response)
        # Template renders the empty-state block when filtered count == 0.
        assert "No expenses in this date range" in body
        # The Filtered Period header must NOT appear for an empty result.
        assert "Filtered Period" not in body

    def test_stats_page_loads_without_crash_when_user_has_no_expenses(
        self, empty_client
    ):
        """
        A user with zero expenses must see the no-expenses empty state on the
        unfiltered stats page — the template must not crash accessing None values.
        """
        response = empty_client.get("/profile/stats")

        assert response.status_code == 200
        body = _html(response)
        assert "No expenses recorded yet" in body


# ===========================================================================
# 5. /profile/stats — filter UI elements
# ===========================================================================

class TestStatsFilterUI:
    """Verify that the stats page filter controls reflect the active state."""

    def test_filter_inputs_prepopulated_with_active_params(
        self, seeded_client
    ):
        """
        The from/to date inputs on /profile/stats must carry the active
        filter values so the user can see and adjust them.
        """
        response = seeded_client.get(
            f"/profile/stats?from={DATE_JAN}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        body = _html(response)
        assert f'value="{DATE_JAN}"' in body
        assert f'value="{DATE_MAR}"' in body

    def test_clear_link_present_when_filter_active(self, seeded_client):
        """
        The 'Clear' link must appear on /profile/stats when a filter is active.
        """
        response = seeded_client.get(f"/profile/stats?from={DATE_JAN}")

        assert response.status_code == 200
        assert "Clear" in _html(response)

    def test_active_filter_label_present_on_stats_page(self, seeded_client):
        """
        The 'Showing results' label must appear on /profile/stats when a
        filter is active, consistent with the other sub-routes.
        """
        response = seeded_client.get(
            f"/profile/stats?from={DATE_FEB}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        body = _html(response)
        assert "Showing results" in body


# ===========================================================================
# 6. /profile/categories — date filter behaviour
# ===========================================================================

class TestCategoriesDateFilter:
    """Behaviour tests for GET /profile/categories with date params."""

    def test_no_params_shows_all_category_totals(self, seeded_client):
        """
        Without date params, every category with expenses must appear and
        its total must reflect all-time spending.
        """
        response = seeded_client.get("/profile/categories")

        assert response.status_code == 200
        body = _html(response)
        assert "Food"   in body
        assert "Travel" in body
        assert "Bills"  in body

    def test_date_filter_limits_category_totals_to_range(
        self, seeded_client
    ):
        """
        When ?from=DATE&to=DATE is supplied, only expenses in that range
        should contribute to the category totals.

        Seeded: Food=Jan 100, Travel=Feb 200, Bills=Mar 300.
        Range [Jan, Jan] → Food shows 100.00, Travel and Bills show 0.
        """
        response = seeded_client.get(
            f"/profile/categories?from={DATE_JAN}&to={DATE_JAN}"
        )

        assert response.status_code == 200
        body = _html(response)
        # Food must show its amount for the filtered period.
        assert "100.00" in body

    def test_grand_total_reflects_only_filtered_range(self, seeded_client):
        """
        The grand total on /profile/categories must be the sum of expenses
        within the active date range, not all-time total.

        Range [Feb, Feb] → grand total = 200.00.
        """
        response = seeded_client.get(
            f"/profile/categories?from={DATE_FEB}&to={DATE_FEB}"
        )

        assert response.status_code == 200
        body = _html(response)
        # 200.00 must appear (the Travel expense for Feb).
        assert "200.00" in body

    def test_categories_outside_filter_show_zero_expenses(
        self, seeded_client
    ):
        """
        Categories that have no expenses in the filtered date range must show
        zero count and zero total — the category row itself may still appear
        but must not carry stale totals from outside the range.
        """
        response = seeded_client.get(
            f"/profile/categories?from={DATE_JAN}&to={DATE_JAN}"
        )

        assert response.status_code == 200
        # The March 300.00 amount must not leak into the filtered view.
        assert "300.00" not in _html(response)

    def test_categories_page_loads_for_user_with_no_expenses(
        self, empty_client
    ):
        """
        A user with no expenses must see an empty-state message rather than
        a crash when visiting /profile/categories.
        """
        response = empty_client.get("/profile/categories")

        assert response.status_code == 200
        assert "No expenses recorded yet" in _html(response)

    def test_categories_page_with_filter_and_no_matches_shows_empty_state(
        self, seeded_client
    ):
        """
        When the date range matches no expenses, category cards must show
        zero counts and the page must not crash.
        """
        response = seeded_client.get(
            "/profile/categories?from=2030-01-01&to=2030-12-31"
        )

        assert response.status_code == 200
        # No amounts from seeded expenses should appear.
        body = _html(response)
        assert "100.00" not in body
        assert "200.00" not in body
        assert "300.00" not in body


# ===========================================================================
# 7. /profile/categories — filter UI elements
# ===========================================================================

class TestCategoriesFilterUI:
    """Verify that /profile/categories renders filter UI state correctly."""

    def test_filter_inputs_prepopulated_with_active_params(
        self, seeded_client
    ):
        """
        The from/to inputs on /profile/categories must pre-populate with
        the active filter values.
        """
        response = seeded_client.get(
            f"/profile/categories?from={DATE_JAN}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        body = _html(response)
        assert f'value="{DATE_JAN}"' in body
        assert f'value="{DATE_MAR}"' in body

    def test_clear_link_present_when_filter_active(self, seeded_client):
        """
        The 'Clear' link must appear when a date filter is active.
        """
        response = seeded_client.get(f"/profile/categories?to={DATE_MAR}")

        assert response.status_code == 200
        assert "Clear" in _html(response)

    def test_active_filter_label_present_on_categories_page(
        self, seeded_client
    ):
        """
        The 'Showing results' label must appear on /profile/categories when
        a date filter is active.
        """
        response = seeded_client.get(
            f"/profile/categories?from={DATE_FEB}&to={DATE_MAR}"
        )

        assert response.status_code == 200
        body = _html(response)
        assert "Showing results" in body

    def test_clear_link_absent_when_no_filter_active(self, seeded_client):
        """
        The 'Clear' link must NOT appear on /profile/categories when no
        filter params are present.
        """
        response = seeded_client.get("/profile/categories")

        assert response.status_code == 200
        assert '<a class="filter-clear"' not in _html(response)


# ===========================================================================
# 8. Malformed date handling — all three routes
# ===========================================================================

class TestMalformedDateHandling:
    """
    When a date value does not match YYYY-MM-DD the application must flash
    an error and return unfiltered results — no crash, no 500.
    """

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_malformed_from_date_returns_200(
        self, seeded_client, path
    ):
        """
        A malformed ?from= value must not crash the server; the route must
        still return HTTP 200.
        """
        response = seeded_client.get(f"{path}?from=not-a-date")

        assert response.status_code == 200

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_malformed_to_date_returns_200(
        self, seeded_client, path
    ):
        """
        A malformed ?to= value must not crash the server.
        """
        response = seeded_client.get(f"{path}?to=20-Jan-2024")

        assert response.status_code == 200

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_malformed_date_flashes_error_message(
        self, seeded_client, path
    ):
        """
        After a malformed date param, the rendered page must contain the
        flash error message so the user knows what went wrong.
        """
        response = seeded_client.get(f"{path}?from=not-a-date")

        assert response.status_code == 200
        assert "Invalid date format" in _html(response)

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_malformed_date_returns_unfiltered_results(
        self, seeded_client, path
    ):
        """
        With a malformed date, the route must fall back to unfiltered results
        so that the user still sees their data while the error is displayed.

        For /profile/history this means all expense descriptions appear.
        For /profile/stats this means the This Month / All Time sections appear.
        For /profile/categories this means all category names appear.
        """
        response = seeded_client.get(f"{path}?from=not-a-date")

        assert response.status_code == 200
        body = _html(response)

        if path == "/profile/history":
            assert "January groceries" in body
            assert "February flight"   in body
            assert "March electricity" in body
        elif path == "/profile/stats":
            # Unfiltered stats page shows This Month and All Time.
            assert "This Month" in body
            assert "All Time"   in body
        elif path == "/profile/categories":
            assert "Food"   in body
            assert "Travel" in body
            assert "Bills"  in body

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_partial_date_string_treated_as_malformed(
        self, seeded_client, path
    ):
        """
        An incomplete date string such as '2024-01' must be treated as
        malformed and trigger the error flash (it does not match YYYY-MM-DD).
        """
        response = seeded_client.get(f"{path}?from=2024-01")

        assert response.status_code == 200
        assert "Invalid date format" in _html(response)

    @pytest.mark.parametrize("path", [
        "/profile/history",
        "/profile/stats",
        "/profile/categories",
    ])
    def test_sql_injection_attempt_treated_as_malformed_date(
        self, seeded_client, path
    ):
        """
        A value like '1 OR 1=1' does not match YYYY-MM-DD and must be
        rejected as a malformed date without causing a server error.
        """
        response = seeded_client.get(f"{path}?from=1+OR+1%3D1")

        assert response.status_code == 200
        assert "Invalid date format" in _html(response)


# ===========================================================================
# 9. Data isolation — users only see their own expenses
# ===========================================================================

class TestUserDataIsolation:
    """
    Each user's date-filtered results must be isolated from other users'
    expenses even when the date ranges overlap.
    """

    def test_history_filter_returns_only_own_expenses(self, app, db_conn):
        """
        Two users with overlapping expense dates: each user's history must
        contain only their own expenses, even when the same date range is used.
        """
        # Create user A.
        cur = db_conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("UserA", "usera@example.com", generate_password_hash("pass1234")),
        )
        db_conn.commit()
        user_a_id = cur.lastrowid

        # Create user B.
        cur = db_conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("UserB", "userb@example.com", generate_password_hash("pass1234")),
        )
        db_conn.commit()
        user_b_id = cur.lastrowid

        # Add a category for each.
        for uid in (user_a_id, user_b_id):
            db_conn.execute(
                "INSERT INTO categories (user_id, name) VALUES (?, ?)",
                (uid, "Food"),
            )
        db_conn.commit()

        cat_a = db_conn.execute(
            "SELECT id FROM categories WHERE user_id=?", (user_a_id,)
        ).fetchone()["id"]
        cat_b = db_conn.execute(
            "SELECT id FROM categories WHERE user_id=?", (user_b_id,)
        ).fetchone()["id"]

        # Both users have an expense on the same date.
        db_conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_a_id, cat_a, 111.11, DATE_FEB, "UserA only expense"),
        )
        db_conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_b_id, cat_b, 999.99, DATE_FEB, "UserB only expense"),
        )
        db_conn.commit()

        # Log in as User A.
        client_a = app.test_client()
        with client_a.session_transaction() as sess:
            sess["user_id"]   = user_a_id
            sess["user_name"] = "UserA"

        response = client_a.get(f"/profile/history?from={DATE_FEB}&to={DATE_FEB}")

        assert response.status_code == 200
        body = _html(response)
        assert "UserA only expense" in body
        assert "UserB only expense" not in body
