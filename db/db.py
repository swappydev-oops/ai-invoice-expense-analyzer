import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    with open("db/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
