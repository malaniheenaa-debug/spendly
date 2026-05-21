---
name: project-date-filter-feature
description: Step 06 date filter feature for /profile/history, /profile/stats, /profile/categories — static analysis of test results
metadata:
  type: project
---

Step 06 implements optional `?from=YYYY-MM-DD&to=YYYY-MM-DD` query params on three profile sub-routes. Test file: `tests/test_date_filter.py` (70 individual test cases across 9 classes).

Static analysis (code review, no live execution) identified these failure categories:

**Likely PASSING (implementation matches test expectations):**
- All auth guard tests (redirects to /login for unauthenticated requests)
- History date filtering (SQL uses correct `>=` / `<=` with IS NULL fallback)
- History empty states ("No transactions yet" present in history.html)
- History filter UI (value pre-population, Clear link, filter-active-label, Showing results)
- Stats date filtering logic (filtered/all_time/this_month branching correct)
- Stats UI (Clear link, Showing results label, input pre-population)
- Categories date filtering via LEFT JOIN ON clause (correctly scope filtered dates)
- Categories UI (Clear link, Showing results, input pre-population)
- Malformed date handling (flash + fallback to unfiltered)
- User data isolation (WHERE user_id = ? on all queries)

**Likely FAILING — Bug in implementation:**
1. `test_zero_matching_expenses_shows_empty_state_without_crash` in TestStatsDateFilter:
   - Test asserts `"Filtered Period" not in body` when filtered count == 0.
   - Template stats.html line 223 renders "Filtered Period" ONLY inside the `{% else %}` branch of `{% if filtered['count'] == 0 %}`, so it does NOT appear when count == 0. This test should PASS.

2. `test_categories_outside_filter_show_zero_expenses` in TestCategoriesDateFilter:
   - Asserts `"300.00" not in body`. With filter [Jan, Jan], Bills has 0 expenses. The template renders `"%.2f"|format(cat['total'])` which would be "0.00" for Bills. 300.00 would not appear. Should PASS.

**One definite FAILING test — Test assertion issue:**
- `test_filtered_stats_reflect_only_matching_expenses`: asserts `">1<" in body`. The template renders `<span class="stat-value">{{ filtered['count'] }}</span>` which produces `<span class="stat-value">1</span>` — no `>1<` substring exists because there is whitespace: the actual rendered output will be `>1<` with possible newlines/spaces. However Jinja2 renders `{{ filtered['count'] }}` inline so actual output is `>1<` with no spaces. This likely PASSES.

**Critical potential failure:**
- `test_categories_page_with_filter_and_no_matches_shows_empty_state`: filter [2030-01-01, 2030-12-31] — all categories have count=0. Template uses `{% set has_expenses = categories | selectattr('count', 'gt', 0) | list | length > 0 %}` — with all counts 0, `has_expenses` is False, so it shows the "No expenses recorded yet" empty state. BUT the test only asserts that seeded amounts (100.00, 200.00, 300.00) are not in body — this PASSES.

**Why:** This is a complex Step 06 feature with 70 tests. Implementation appears complete.

**How to apply:** When running these tests, expect near-full pass rate. Primary risk area is the stats empty-state "Filtered Period" visibility logic.
