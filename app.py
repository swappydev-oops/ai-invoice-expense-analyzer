import streamlit as st
from auth.auth import require_login
from db.company_repo import get_all_companies, create_company, update_company, toggle_company
from db.user_repo import get_all_users, create_user, update_user_role, toggle_user

st.set_page_config("Admin Panel", layout="wide")
require_login()


def toast(msg):
    try:
        st.toast(msg, icon="✅")
    except:
        st.success(msg)


with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_name}**")

    with st.expander("🛠 Admin Panel"):
        if st.button("User Details"):
            st.session_state.page = "users"
        if st.button("Company Details"):
            st.session_state.page = "companies"


if "page" not in st.session_state:
    st.session_state.page = "users"

# =================================================
# USER CRUD
# =================================================
if st.session_state.page == "users":
    st.title("👥 User Management")

    with st.expander("➕ Create User"):
        user_name = st.text_input("Username")
        first = st.text_input("First Name")
        last = st.text_input("Last Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        companies = get_all_companies()
        company_map = {c["company_name"]: c["id"] for c in companies}
        company = st.selectbox("Company", list(company_map.keys()))
        role = st.selectbox("Role", ["admin", "user"])

        if st.button("Create User"):
            create_user(
                {
                    "user_name": user_name,
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "password": password,
                    "company_id": company_map[company],
                    "role": role
                },
                st.session_state.user_name
            )
            toast("User created")
            st.rerun()

    users = get_all_users()

    for u in users:
        cols = st.columns([3, 3, 2, 2])
        cols[0].write(u["user_name"])
        cols[1].write(u["company_name"])
        cols[2].write(u["role"])
        if cols[3].button("Disable" if u["is_active"] else "Enable", key=u["id"]):
            toggle_user(u["id"], not u["is_active"], st.session_state.user_name)
            st.rerun()


# =================================================
# COMPANY CRUD
# =================================================
if st.session_state.page == "companies":
    st.title("🏢 Company Management")

    with st.expander("➕ Create Company"):
        name = st.text_input("Company Name")
        gst = st.text_input("GST Number")
        plan = st.selectbox("Plan", ["Free", "Pro"])

        if st.button("Create Company"):
            create_company(name, gst, plan, st.session_state.user_name)
            toast("Company created")
            st.rerun()

    companies = get_all_companies()

    for c in companies:
        cols = st.columns([3, 2, 2, 2])
        cols[0].write(c["company_name"])
        cols[1].write(c["subscription_plan"])
        cols[2].write("Active" if c["is_active"] else "Disabled")
        if cols[3].button("Disable" if c["is_active"] else "Enable", key=f"c{c['id']}"):
            toggle_company(c["id"], not c["is_active"], st.session_state.user_name)
            st.rerun()
