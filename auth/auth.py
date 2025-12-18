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
def load_css():
    st.markdown("""
    <style>
    /* Remove Streamlit padding */
    section.main > div {
        padding-top: 2rem;
    }

    /* Animated card */
    .auth-card {
        max-width: 420px;
        margin: auto;
        margin-top: 10vh;
        padding: 2.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #ffffff, #f3f6fa);
        box-shadow: 0 25px 50px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
        animation: fadeIn 0.8s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Animated invoice lines */
    .invoice-line {
        position: absolute;
        width: 80%;
        height: 8px;
        background: linear-gradient(
            90deg,
            rgba(200,200,200,0.2),
            rgba(180,180,180,0.6),
            rgba(200,200,200,0.2)
        );
        border-radius: 6px;
        animation: scan 3s infinite linear;
    }

    @keyframes scan {
        from { left: -80%; }
        to { left: 120%; }
    }

    .invoice-line:nth-child(1) { top: 20px; animation-delay: 0s; }
    .invoice-line:nth-child(2) { top: 45px; animation-delay: 1s; }
    .invoice-line:nth-child(3) { top: 70px; animation-delay: 2s; }

    .title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- LOGIN ----------------
def login_ui():
    load_css()

    st.markdown("""
    <div class="auth-card">
        <div class="invoice-line"></div>
        <div class="invoice-line"></div>
        <div class="invoice-line"></div>

        <div class="title">🔐 Login</div>
        <div class="subtitle">Access your invoice dashboard</div>
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
            time.sleep(0.4)
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- REGISTER ----------------
def register_ui():
    load_css()

    st.markdown("""
    <div class="auth-card">
        <div class="invoice-line"></div>
        <div class="invoice-line"></div>
        <div class="invoice-line"></div>

        <div class="title">📝 Register</div>
        <div class="subtitle">Create your free account</div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pass")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register", use_container_width=True):
        if password != confirm:
            st.error("Passwords do not match")
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
        mode = st.radio("", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            login_ui()
        else:
            register_ui()
        st.stop()
