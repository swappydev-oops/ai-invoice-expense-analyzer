import streamlit as st
import sqlite3
import hashlib
import time

# ---------------- DB ----------------
def get_conn():
    return sqlite3.connect("data.db", check_same_thread=False)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- HTML UI ----------------
def render_auth_ui(mode="login"):
    st.components.v1.html(
        f"""
        <html>
        <head>
        <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(120deg,#0f2027,#203a43,#2c5364);
            background-size: 400% 400%;
            animation: bg 12s ease infinite;
            color: white;
        }}

        @keyframes bg {{
            0% {{background-position:0% 50%;}}
            50% {{background-position:100% 50%;}}
            100% {{background-position:0% 50%;}}
        }}

        .card {{
            width: 380px;
            margin: 12vh auto;
            background: white;
            color: black;
            padding: 30px;
            border-radius: 14px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.4);
        }}

        h2 {{
            text-align: center;
            margin-bottom: 10px;
        }}

        p {{
            text-align: center;
            color: #666;
        }}

        input {{
            width: 100%;
            padding: 12px;
            margin-top: 12px;
            border-radius: 8px;
            border: 1px solid #ddd;
            font-size: 14px;
        }}

        button {{
            width: 100%;
            margin-top: 20px;
            padding: 12px;
            background: #2c5364;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            cursor: pointer;
        }}

        .invoice {{
            position: absolute;
            width: 160px;
            height: 220px;
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            animation: float 18s linear infinite;
        }}

        @keyframes float {{
            from {{ transform: translateY(110vh); }}
            to {{ transform: translateY(-130vh); }}
        }}
        </style>
        </head>

        <body>
            <div class="invoice" style="left:10%;"></div>
            <div class="invoice" style="left:40%; animation-duration:22s;"></div>
            <div class="invoice" style="left:70%; animation-duration:26s;"></div>

            <div class="card">
                <h2>{'Login' if mode=='login' else 'Register'}</h2>
                <p>AI Invoice & Expense Analyzer</p>

                <form method="GET">
                    <input name="email" placeholder="Email" />
                    <input name="password" type="password" placeholder="Password" />
                    {"<input name='confirm' type='password' placeholder='Confirm Password' />" if mode=="register" else ""}
                    <button type="submit">{'Login' if mode=='login' else 'Register'}</button>
                </form>
            </div>
        </body>
        </html>
        """,
        height=700,
    )

# ---------------- AUTH LOGIC ----------------
def require_login():
    params = st.query_params
    email = params.get("email")
    password = params.get("password")
    confirm = params.get("confirm")

    mode = st.radio("", ["Login", "Register"], horizontal=True)

    if not email:
        render_auth_ui("login" if mode == "Login" else "register")
        st.stop()

    conn = get_conn()
    cur = conn.cursor()

    if mode == "Login":
        cur.execute(
            "SELECT id,email,role,plan FROM users WHERE email=? AND password=?",
            (email, hash_password(password))
        )
        user = cur.fetchone()

        if user:
            st.session_state.user_id = user[0]
            st.session_state.user_email = user[1]
            st.session_state.role = user[2]
            st.session_state.plan = user[3]
            st.query_params.clear()
            st.success("Login successful 🎉")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Invalid credentials")

    else:
        if password != confirm:
            st.error("Passwords do not match")
        else:
            try:
                cur.execute(
                    "INSERT INTO users(email,password,role,plan) VALUES(?,?,?,?)",
                    (email, hash_password(password), "user", "free")
                )
                conn.commit()
                st.success("Account created 🎉")
            except sqlite3.IntegrityError:
                st.error("Email already exists")

    conn.close()
    st.stop()
