import streamlit as st
import re
from utils.api_client import APIClient
from utils.ui_components import apply_auth_css, show_error, show_success

def render_signin():
    apply_auth_css()
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'><h1 class='brand-font'>ITTICKET</h1><p class='tech-label'>Support Portal</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### Sign In")
            username = st.text_input("Username", key="si_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="si_pass", placeholder="Enter password")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Sign In", use_container_width=True):
                    if not username or not password:
                        show_error("Both fields are required.")
                    else:
                        api = APIClient()
                        result = api.signin(username, password)
                        if result:
                            st.session_state["username"] = result.get("username", username)
                            st.session_state["user_id"] = result.get("user_id", 1)
                            st.session_state["access_token"] = result.get("access_token", "mock")
                            st.session_state["current_page"] = "Dashboard"
                            st.rerun()
            with c2:
                if st.button("Create Account", use_container_width=True):
                    st.session_state["auth_page"] = "signup"
                    st.rerun()

def render_signup():
    apply_auth_css()
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'><h1 class='brand-font'>ITTICKET</h1><p class='tech-label'>Support Portal</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### Sign Up")
            username = st.text_input("Username", key="su_user", placeholder="Choose username")
            email = st.text_input("Email", key="su_email", placeholder="Enter email")
            password = st.text_input("Password", type="password", key="su_pass", placeholder="Choose password")
            password_confirm = st.text_input("Confirm Password", type="password", key="su_pass_c", placeholder="Confirm password")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Sign Up", use_container_width=True):
                    if not username or not email or not password or not password_confirm:
                        show_error("All fields are required.")
                    elif "@" not in email or "." not in email:
                        show_error("Please enter a valid email address.")
                    elif len(password) < 8:
                        show_error("Password must be at least 8 characters.")
                    elif not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
                        show_error("Password must contain uppercase, lowercase, and a number.")
                    elif password != password_confirm:
                        show_error("Passwords do not match.")
                    else:
                        api = APIClient()
                        result = api.signup(username, email, password)
                        if result:
                            show_success("Account created successfully!")
                            st.session_state["auth_page"] = "signin"
                            st.rerun()
            with c2:
                if st.button("Back to Sign In", use_container_width=True):
                    st.session_state["auth_page"] = "signin"
                    st.rerun()
