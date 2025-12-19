-- USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    company_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VENDORS
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gstin TEXT,
    UNIQUE(name, gstin)
);

-- INVOICES
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    invoice_number TEXT NOT NULL,
    invoice_date DATE,
    subtotal REAL,
    gst_percent REAL,
    gst_amount REAL,
    total_amount REAL,
    category TEXT,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (user_id, invoice_number),

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- VALIDATIONS
CREATE TABLE IF NOT EXISTS invoice_validations (
    invoice_id INTEGER PRIMARY KEY,
    date_valid BOOLEAN,
    gst_valid BOOLEAN,
    total_valid BOOLEAN,
    vendor_valid BOOLEAN,
    notes TEXT,

    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

-- AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Company Table
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    gst_number TEXT,
    plan TEXT DEFAULT 'free',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migrate users into new table
INSERT INTO companies (name)
SELECT DISTINCT company_name
FROM users
WHERE company_name IS NOT NULL
  AND company_name != '';

  -- Temporary User Table
  CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    company_id INTEGER NOT NULL,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

INSERT INTO users_new (
    id,
    email,
    password_hash,
    company_id,
    created_at
)
SELECT
    u.id,
    u.email,
    u.password_hash,
    c.id AS company_id,
    u.created_at
FROM users u
JOIN companies c
  ON u.company_name = c.name;

  -- Test purpose

DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- Create Index
CREATE INDEX idx_users_company_id ON users(company_id);

