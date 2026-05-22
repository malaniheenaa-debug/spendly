import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), "spendly.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
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
    conn.commit()
    conn.close()


def get_categories(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()


def add_expense(user_id, category_id, amount, date, description):
    conn = get_db()
    try:
        if category_id is not None:
            row = conn.execute(
                "SELECT id FROM categories WHERE id = ? AND user_id = ?",
                (category_id, user_id)
            ).fetchone()
            if row is None:
                category_id = None
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, category_id, amount, date, description)
        )
        conn.commit()
    finally:
        conn.close()


def get_expense(expense_id, user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, user_id, category_id, amount, date, description FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id)
        ).fetchone()
    finally:
        conn.close()


def update_expense(expense_id, user_id, category_id, amount, date, description):
    conn = get_db()
    try:
        conn.execute(
            """UPDATE expenses
               SET category_id = ?, amount = ?, date = ?, description = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?""",
            (category_id, amount, date, description, expense_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_expense(expense_id, user_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    conn.executescript("""
        INSERT OR IGNORE INTO users (id, name, email, password)
        VALUES (1, 'Demo User', 'demo@spendly.com', 'hashed_password');

        INSERT OR IGNORE INTO categories (id, user_id, name) VALUES
            (1, 1, 'Food'),
            (2, 1, 'Travel'),
            (3, 1, 'Bills'),
            (4, 1, 'Entertainment');

        INSERT OR IGNORE INTO expenses (user_id, category_id, amount, date, description) VALUES
            (1, 1, 450.00,  '2026-05-01', 'Grocery run'),
            (1, 2, 1200.00, '2026-05-03', 'Cab to airport'),
            (1, 3, 3500.00, '2026-05-05', 'Electricity bill'),
            (1, 1, 320.00,  '2026-05-07', 'Restaurant dinner'),
            (1, 4, 800.00,  '2026-05-09', 'Movie tickets'),
            (1, 2, 250.00,  '2026-05-10', 'Auto rickshaw');
    """)
    conn.commit()
    conn.close()
