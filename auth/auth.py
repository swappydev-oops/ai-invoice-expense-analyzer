import streamlit as st
import hashlib
import time
from db.db import get_connection

# -------------------------------------------------
# Toast Compatibility Helper (VERY IMPORTANT)
# -------------------------------------------------
def show_toast(message, icon="✅"):
    if hasattr(st, "toast"):
        st.toast(message, icon=icon)
    else:
        st.success(message)

# -------------------------------------------------
# Password Utilities
# -------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------------------------------
# Database Operations
# -------------------------------------------------
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
        (email,)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(email, password, company_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (email, password_hash, company_name)
        VALUES (?, ?, ?)
        """,
        (email, hash_password(password), company_name)
    )
    conn.commit()
    conn.close()

# -------------------------------------------------
# Login UI
# -------------------------------------------------
def login_ui():
    st.subheader("🔐 Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        user = get_user_by_email(email)

        if not user:
            st.error("User not found")
            return

        user_id, password_hash = user

        if hash_password(password) != password_hash:
            st.error("Incorrect password")
            return

        # Set session state
        st.session_state.user_id = user_id
        st.session_state.user_email = email

        show_toast("Login successful 🎉")
        time.sleep(0.3)
        st.rerun()

# -------------------------------------------------
# Register UI
# -------------------------------------------------
def register_ui():
    st.subheader("📝 Register")

    email = st.text_input("Email", key="register_email")
    company = st.text_input("Company Name", key="register_company")
    password = st.text_input("Password", type="password", key="register_password")
    confirm = st.text_input("Confirm Password", type="password", key="register_confirm")

    if st.button("Register", key="register_button"):
        if password != confirm:
            st.error("Passwords do not match")
            return

        if get_user_by_email(email):
            st.error("User already exists")
            return

        create_user(email, password, company)
        st.success("Account created successfully. Please login.")

# -------------------------------------------------
# Authentication Gate
# -------------------------------------------------
def require_login():
    if "user_id" not in st.session_state:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            login_ui()
        with tab2:
            register_ui()
        st.stop()
