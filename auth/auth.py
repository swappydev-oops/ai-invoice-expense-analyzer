import streamlit as st
import sqlite3
import hashlib
import time

# -------------------------------------------------
# DB connection
# -------------------------------------------------
def get_conn():
    return sqlite3.connect("data.db", check_same_thread=False)

# -------------------------------------------------
# Password hash
# -------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------------------------------
# Animated Background + UI CSS
# -------------------------------------------------
def load_auth_ui_css():
    st.markdown(
        """
        <style>
        /* -------- Page Background -------- */
        .stApp {
            background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* -------- Floating Invoice Cards -------- */
        .invoice-bg {
            position: fixed;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
        }

        .invoice {
            position: absolute;
            width: 180px;
            height: 240px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            animation: float 25s linear infinite;
        }

        .invoice::before {
            content: "";
            position: absolute;
            top: 15px;
            left: 15px;
            right: 15px;
            height: 10px;
            background: rgba(255,255,255,0.3);
            border-radius: 6px;
        }

        @keyframes float {
            from { transform: translateY(110vh); }
            to { transform: translateY(-120vh); }
        }

        /* -------- Auth Card -------- */
        .auth-card {
            position: relative;
            z-index: 10;
            max-width: 420px;
            margin: auto;
            margin-top: 8vh;
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0px 20px 40px rgba(0,0,0,0.3);
        }

        .auth-title {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .auth-subtitle {
            text-align: center;
            color: #6c757d;
            margin-bottom: 2rem;
        }

        </style>

        <!-- Floating invoice background -->
        <div class="invoice-bg">
            <div class="invoice" style="left:10%; animation-duration: 18s;"></div>
            <div class="invoice" style="left:30%; animation-duration: 22s;"></div>
            <div class="invoice" style="left:50%; animation-duration: 26s;"></div>
            <div class="invoice" style="left:70%; animation-duration: 20s;"></div>
            <div class="invoice" style="left:85%; animation-duration: 24s;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------
# Login UI
# -------------------------------------------------
def login_ui():
    load_auth_ui_css()

    st.markdown(
        """
        <div class="auth-card">
            <div class="auth-title">Welcome Back 👋</div>
            <div class="auth-subtitle">Login to manage your invoices</div>
        """,
        unsafe_allow_html=True
    )

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", use_container_width=True):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, role, plan FROM users WHERE email = ? AND password = ?",
            (email, hash_password(password))
        )
        user = cursor.fetchone()
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
            st.error("Invalid email or password")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Register UI
# -------------------------------------------------
def register_ui():
    load_auth_ui_css()

    st.markdown(
        """
        <div class="auth-card">
            <div class="auth-title">Create Account ✨</div>
            <div class="auth-subtitle">Start managing your invoices smarter</div>
        """,
        unsafe_allow_html=True
    )

    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Register", use_container_width=True):
        conn = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (email, password, role, plan)
                VALUES (?, ?, 'user', 'free')
                """,
                (email, hash_password(password))
            )
            conn.commit()
            st.success("Account created successfully 🎉")
        except sqlite3.IntegrityError:
            st.error("Email already exists")
        finally:
            conn.close()

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Auth Gate
# -------------------------------------------------
def require_login():
    if "user_id" not in st.session_state:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        with tab1:
            login_ui()
        with tab2:
            register_ui()
        st.stop()
