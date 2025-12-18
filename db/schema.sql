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

ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free';

