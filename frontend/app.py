import streamlit as st
st.set_page_config(page_title="IT Ticket Resolution", page_icon="🎫", layout="wide")

from utils.session_manager import init_session_state, is_authenticated, check_query_params, navigate_to
from utils.ui_components import apply_theme
from config import PAGE_NAMES, BACKEND_URL, ADMIN_USERS

def main():
    init_session_state()
    check_query_params()
    apply_theme()

    if not is_authenticated():
        from pages.auth import render_signin, render_signup
        if st.session_state.get("auth_page") == "signup":
            render_signup()
        else:
            render_signin()
        st.stop()

    def on_nav_change():
        st.session_state["current_page"] = st.session_state["nav_radio"]
        st.query_params["page"] = st.session_state["nav_radio"]

    with st.sidebar:
        st.markdown('<p class="tech-label">Platform</p>', unsafe_allow_html=True)
        st.markdown('<p class="brand-font">IT TICKET</p>', unsafe_allow_html=True)
        st.markdown('<p class="tech-label" style="margin-top:-5px;">Resolution Engine</p>', unsafe_allow_html=True)
        st.divider()

        current_username = st.session_state.get('username', '').lower()
        admin_users_lower = [u.lower() for u in ADMIN_USERS]
        is_admin = current_username in admin_users_lower

        if is_admin:
            available_pages = PAGE_NAMES
        else:
            available_pages = [p for p in PAGE_NAMES if p not in ["Historical Tickets", "Analytics"]]

        current_page = st.session_state.get("current_page", available_pages[0])
        # If accessing ticket detail, it might not be in sidebar list, so default to My Tickets or keep it hidden
        if current_page not in available_pages and current_page != "Ticket Detail":
            current_page = available_pages[0]
        
        display_page = current_page if current_page in available_pages else "My Tickets"
        if "nav_radio" not in st.session_state or st.session_state["nav_radio"] != display_page:
            st.session_state["nav_radio"] = display_page

        st.radio(
            "Navigation",
            available_pages,
            key="nav_radio",
            on_change=on_nav_change,
            label_visibility="collapsed",
        )

        st.divider()

        st.markdown(
            f"<div style='font-size:11px;color:#999;letter-spacing:0.05em;'>"
            f"<p><strong>API ENDPOINT</strong><br/>{BACKEND_URL}</p>"
            f"<p>Signed in as <strong>{st.session_state.get('username','')}</strong></p></div>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("confirm_signout"):
            st.warning("Are you sure you want to sign out?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", type="primary", use_container_width=True):
                from utils.session_manager import clear_session
                clear_session()
                st.session_state["confirm_signout"] = False
                st.rerun()
            if c2.button("No", use_container_width=True):
                st.session_state["confirm_signout"] = False
                st.rerun()
        else:
            if st.button("Sign Out", key="sign_out_btn"):
                st.session_state["confirm_signout"] = True
                st.rerun()

    from pages import dashboard, create_ticket, my_tickets, historical_tickets, analytics, ticket_detail

    # Routing
    page_map = {
        "Dashboard": dashboard.render,
        "Create Ticket": create_ticket.render,
        "My Tickets": my_tickets.render,
        "Historical Tickets": historical_tickets.render,
        "Analytics": analytics.render,
        "Ticket Detail": ticket_detail.render
    }

    current = st.session_state.get("current_page", "Dashboard")
    
    current_username = st.session_state.get('username', '').lower()
    admin_users_lower = [u.lower() for u in ADMIN_USERS]
    is_admin = current_username in admin_users_lower

    if not is_admin and current in ["Historical Tickets", "Analytics"]:
        st.error("🔒 You do not have permission to view this page.")
        st.stop()
        
    page_map.get(current, dashboard.render)()

if __name__ == "__main__":
    main()
