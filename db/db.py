import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def column_exists(conn, table, column):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def migrate_company_schema(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        gst_number TEXT,
        plan TEXT DEFAULT 'free',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    if not column_exists(conn, "users", "company_name"):
        return

    cur.execute("""
    INSERT OR IGNORE INTO companies (name)
    SELECT DISTINCT company_name
    FROM users
    WHERE company_name IS NOT NULL AND company_name != ''
    """)

    cur.execute("""
    CREATE TABLE users_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        company_id INTEGER NOT NULL,
        role TEXT DEFAULT 'user',
        plan TEXT DEFAULT 'free',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )
    """)

    cur.execute("""
    INSERT INTO users_new
    SELECT
        u.id,
        u.email,
        u.password_hash,
        c.id,
        u.role,
        u.plan,
        1,
        u.created_at
    FROM users u
    JOIN companies c ON u.company_name = c.name
    """)

    cur.execute("DROP TABLE users")
    cur.execute("ALTER TABLE users_new RENAME TO users")
    conn.commit()


def init_db():
    conn = get_conn()
    migrate_company_schema(conn)
    conn.close()
