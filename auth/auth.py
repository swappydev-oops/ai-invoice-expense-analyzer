import streamlit as st
import sqlite3
import hashlib

DB_PATH = "db/database.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- LOGIN UI ----------------

def login_ui():
    st.subheader("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, email, role, plan
            FROM users
            WHERE email=? AND password_hash=?
            """,
            (email, hash_password(password)),
        )

        row = cur.fetchone()
        conn.close()

        if row:
            user_id, email, role, plan = row
            st.session_state.logged_in = True
            st.session_state.user_id = user_id
            st.session_state.user_email = email
            st.session_state.role = role
            st.session_state.plan = plan or "free"

            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid email or password")

# ---------------- REGISTER UI ----------------

def register_ui():
    st.subheader("📝 Register")

    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Register"):
        conn = get_conn()
        cur = conn.cursor()

        # First user becomes admin
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        role = "admin" if user_count == 0 else "user"

        try:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, role, plan)
                VALUES (?, ?, ?, ?)
                """,
                (email, hash_password(password), role, "free"),
            )
            conn.commit()
            st.success("Registration successful. Please login.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("User already exists")
        finally:
            conn.close()

# ---------------- AUTH GATE ----------------

def require_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            login_ui()
        with tab2:
            register_ui()
        st.stop()
