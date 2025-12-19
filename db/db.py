import sqlite3
from db.config import DB_PATH

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            invoice_number TEXT NOT NULL,
            vendor TEXT,
            invoice_date TEXT,
            subtotal REAL,
            tax REAL,
            total_amount REAL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, invoice_number)
        )
    """)

    # 1. Create companies table
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

    # 2. Insert companies from existing users
    cur.execute("""
    INSERT OR IGNORE INTO companies (name)
    SELECT DISTINCT company_name
    FROM users
    WHERE company_name IS NOT NULL
      AND company_name != ''
    """)

    # 3. Create new users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users_new (
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

    # 4. Migrate users
    cur.execute("""
    INSERT INTO users_new (
        id, email, password_hash, company_id, role, plan, created_at
    )
    SELECT
        u.id,
        u.email,
        u.password_hash,
        c.id,
        u.role,
        u.plan,
        u.created_at
    FROM users u
    JOIN companies c
      ON u.company_name = c.name
    """)

    # 5. Replace old users table
    cur.execute("DROP TABLE users")
    cur.execute("ALTER TABLE users_new RENAME TO users")

    conn.commit()
    conn.close()
