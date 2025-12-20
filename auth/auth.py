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

        cur.execute("""
            SELECT
                id,
                user_name,
                email,
                company_id,
                role,
                is_active
            FROM users
            WHERE email = %s AND password_hash = %s
        """, (email, password))

        user = cur.fetchone()
        conn.close()

        if not user:
            st.error("Invalid email or password")
            return

        if not user["is_active"]:
            st.error("User is inactive. Contact admin.")
            return

        st.session_state.user_id = user["id"]
        st.session_state.user_name = user["user_name"]
        st.session_state.user_email = user["email"]
        st.session_state.company_id = user["company_id"]
        st.session_state.role = user["role"]

        st.success("Login successful 🎉")
        st.rerun()


def require_login():
    if "user_id" not in st.session_state:
        login_ui()
        st.stop()
