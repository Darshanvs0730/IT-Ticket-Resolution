import streamlit as st
import re
import time
from utils.api_client import APIClient
from utils.ui_components import apply_auth_css, show_error, show_success

def render_signin():
    apply_auth_css()
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'><h1 class='brand-font'>ITTICKET</h1><p class='tech-label'>Support Portal</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### Sign In")
            
            role = st.selectbox("Login as:", ["User", "Admin"])
            username = st.text_input("Username", key="si_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="si_pass", placeholder="Enter password")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Sign In", type="primary", use_container_width=True):
                    if not username or not password:
                        st.warning("Please fill all fields.")
                    else:
                        with st.spinner("Authenticating..."):
                            time.sleep(1) # Realistic delay simulation
                            api = APIClient()
                            result = api.signin(username, password)
                            if result:
                                with st.spinner(f"Loading {role} dashboard..."):
                                    time.sleep(0.5)
                                    st.session_state["username"] = result.get("username", username)
                                    st.session_state["user_id"] = result.get("user_id", 1)
                                    st.session_state["access_token"] = result.get("access_token", "mock")
                                    st.session_state["role"] = role
                                    st.session_state["current_page"] = "Historical Tickets" if role == "Admin" else "Dashboard"
                                    st.rerun()
                            else:
                                st.error("Incorrect username or password.")
            with c2:
                if st.button("Create Account", type="secondary", use_container_width=True):
                    st.session_state["auth_page"] = "signup"
                    st.rerun()
            
            st.markdown("<div style='text-align: center; margin-top: 15px; font-size: 11px; color: #6B7280;'>🔒 Secure enterprise login</div>", unsafe_allow_html=True)

def render_signup():
    apply_auth_css()
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'><h1 class='brand-font'>ITTICKET</h1><p class='tech-label'>Support Portal</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### Sign Up")
            
            role = st.selectbox("Register as:", ["User", "Admin"])
            username = st.text_input("Username", key="su_user", placeholder="Choose username")
            email = st.text_input("Email", key="su_email", placeholder="Enter email")
            password = st.text_input("Password", type="password", key="su_pass", placeholder="Choose password")
            password_confirm = st.text_input("Confirm Password", type="password", key="su_pass_c", placeholder="Confirm password")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Sign Up", type="primary", use_container_width=True):
                    if not username or not email or not password or not password_confirm:
                        st.warning("Please fill all fields.")
                    elif "@" not in email or "." not in email:
                        st.error("Please enter a valid email address format.")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
                        st.error("Password must contain uppercase, lowercase, and a number.")
                    elif password != password_confirm:
                        st.error("Passwords do not match. Please try again.")
                    else:
                        with st.spinner("Creating account..."):
                            time.sleep(1)
                            api = APIClient()
                            result = api.signup(username, email, password)
                            if result:
                                show_success("Account created successfully!")
                                time.sleep(1)
                                st.session_state["auth_page"] = "signin"
                                st.rerun()
            with c2:
                if st.button("Back to Sign In", type="secondary", use_container_width=True):
                    st.session_state["auth_page"] = "signin"
                    st.rerun()
            
            st.markdown("<div style='text-align: center; margin-top: 15px; font-size: 11px; color: #6B7280;'>🔒 Secure enterprise login</div>", unsafe_allow_html=True)
