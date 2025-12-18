import streamlit as st
import sqlite3
import hashlib
import time

# ---------------- DB ----------------
def get_conn():
    return sqlite3.connect("data.db", check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- UI Helpers ----------------
def centered_container(width=3):
    left, center, right = st.columns([1, width, 1])
    return center

# ---------------- LOGIN UI ----------------
def login_ui():
    with centered_container():
        st.markdown("## 🔐 Login")
        st.caption("Access your invoice dashboard")

        email = st.text_input("📧 Email", placeholder="you@company.com")
        password = st.text_input("🔑 Password", type="password")

        if st.button("Login", use_container_width=True):
            with st.spinner("Authenticating..."):
                time.sleep(0.5)
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "SELECT id,email,role,plan FROM users WHERE email=? AND password=?",
                    (email, hash_password(password))
                )
                user = cur.fetchone()
                conn.close()

            if user:
                st.session_state.user_id = user[0]
                st.session_state.user_email = user[1]
                st.session_state.role = user[2]
                st.session_state.plan = user[3]
                st.toast("Login successful 🎉")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("Invalid email or password")

# ---------------- REGISTER UI ----------------
def register_ui():
    with centered_container():
        st.markdown("## 📝 Create Account")
        st.caption("Start managing invoices smarter")

        email = st.text_input("📧 Email", placeholder="you@company.com")
        password = st.text_input("🔑 Password", type="password")
        confirm = st.text_input("🔁 Confirm Password", type="password")

        if password and confirm and password != confirm:
            st.warning("Passwords do not match")

        if st.button("Register", use_container_width=True):
            if password != confirm:
                st.error("Passwords do not match")
                return

            with st.spinner("Creating account..."):
                time.sleep(0.5)
                try:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO users(email,password,role,plan) VALUES(?,?,?,?)",
                        (email, hash_password(password), "user", "free")
                    )
                    conn.commit()
                    conn.close()
                    st.success("Account created successfully 🎉")
                except sqlite3.IntegrityError:
                    st.error("Email already exists")

# ---------------- AUTH GATE ----------------
def require_login():
    if "user_id" not in st.session_state:
        st.markdown(
            """
            <style>
            .block-container {
                padding-top: 6rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        mode = st.radio(
            "",
            ["Login", "Register"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if mode == "Login":
            login_ui()
        else:
            register_ui()

        st.stop()
