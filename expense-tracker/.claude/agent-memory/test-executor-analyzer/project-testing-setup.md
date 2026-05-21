---
name: project-testing-setup
description: Venv location, testing framework details, and test file conventions for the Spendly expense tracker
metadata:
  type: project
---

Spendly uses pytest 8.3.5 + pytest-flask 1.3.0. The venv lives at `C:\Users\TCP\Desktop\expense-tracker\venv\` (one level ABOVE the inner `expense-tracker\` project directory). There is no pytest.ini or pyproject.toml — tests are run from the inner project directory.

Run command (from `C:\Users\TCP\Desktop\expense-tracker\expense-tracker\`):
```
C:\Users\TCP\Desktop\expense-tracker\venv\Scripts\python.exe -m pytest tests/test_date_filter.py -v
```

**Why:** The venv is shared at the repo root level, not inside the Flask app subdirectory. Callers must use the absolute venv Python path.

**How to apply:** Always use the full absolute path to `venv\Scripts\python.exe` when constructing run commands for this project.
