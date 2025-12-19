import streamlit as st
import hashlib
from db.db import get_conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def login_ui():
    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, email, company_id, role, plan, is_active
            FROM users
            WHERE email = ? AND password_hash = ?
            """,
            (email, hash_password(password)),
        )

        user = cur.fetchone()
        conn.close()

        if not user:
            st.error("Invalid email or password")
            return

        if user[5] == 0:
            st.error("User is disabled. Contact admin.")
            return

        # ---- SESSION ----
        st.session_state.user_id = user[0]
        st.session_state.user_email = user[1]
        st.session_state.company_id = user[2]
        st.session_state.role = user[3]
        st.session_state.plan = user[4]
        st.session_state.page = "dashboard"

        st.success("Login successful 🎉")
        st.rerun()


def require_login():
    if "user_id" not in st.session_state:
        login_ui()
        st.stop()
