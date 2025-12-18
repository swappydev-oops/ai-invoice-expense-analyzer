import streamlit as st
import sqlite3
import hashlib
import time

# ---------------- DB ----------------
def get_conn():
    return sqlite3.connect("data.db", check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- CSS ----------------
def load_auth_ui_css():
    st.markdown("""
    <style>
    /* FULL BACKGROUND */
    html, body, .stApp {
        height: 100%;
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* FLOATING INVOICE CARDS */
    .invoice {
        position: fixed;
        width: 160px;
        height: 220px;
        background: rgba(255,255,255,0.08);
        border-radius: 12px;
        animation: float 20s linear infinite;
        z-index: 0;
    }

    .invoice::before {
        content: "";
        position: absolute;
        top: 15px;
        left: 15px;
        right: 15px;
        height: 8px;
        background: rgba(255,255,255,0.3);
        border-radius: 4px;
    }

    @keyframes float {
        from { transform: translateY(110vh); }
        to { transform: translateY(-130vh); }
    }

    /* CARD */
    .auth-card {
        position: relative;
        z-index: 10;
        max-width: 420px;
        margin: auto;
        margin-top: 10vh;
        background: white;
        padding: 2.5rem;
        border-radius: 18px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.35);
    }

    .auth-title {
        text-align: center;
        font-size: 1.9rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .auth-sub {
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    </style>

    <div class="invoice" style="left:10%; animation-duration:18s;"></div>
    <div class="invoice" style="left:30%; animation-duration:22s;"></div>
    <div class="invoice" style="left:50%; animation-duration:26s;"></div>
    <div class="invoice" style="left:70%; animation-duration:20s;"></div>
    <div class="invoice" style="left:85%; animation-duration:24s;"></div>
    """, unsafe_allow_html=True)

# ---------------- LOGIN ----------------
def login_ui():
    st.markdown("""
    <div class="auth-card">
        <div class="auth-title">Welcome Back 👋</div>
        <div class="auth-sub">Login to manage your invoices</div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login", use_container_width=True):
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
            st.success("Login successful 🎉")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- REGISTER ----------------
def register_ui():
    st.markdown("""
    <div class="auth-card">
        <div class="auth-title">Create Account ✨</div>
        <div class="auth-sub">Start managing invoices smarter</div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pass")
    confirm = st.text_input("Confirm Password", type="password")

    if password != confirm:
        st.warning("Passwords do not match")

    if st.button("Register", use_container_width=True):
        if password != confirm:
            st.error("Password mismatch")
        else:
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users(email,password,role,plan) VALUES(?,?,?,?)",
                    (email, hash_password(password), "user", "free")
                )
                conn.commit()
                conn.close()
                st.success("Account created 🎉")
            except sqlite3.IntegrityError:
                st.error("Email already exists")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- AUTH GATE ----------------
def require_login():
    if "user_id" not in st.session_state:
        load_auth_ui_css()

        mode = st.radio(
            "",
            ["Login", "Register"],
            horizontal=True
        )

        if mode == "Login":
            login_ui()
        else:
            register_ui()

        st.stop()
