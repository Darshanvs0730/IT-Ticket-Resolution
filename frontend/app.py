import streamlit as st
st.set_page_config(page_title="IT Ticket Resolution", page_icon="🎫", layout="wide")

from utils.session_manager import init_session_state, is_authenticated, check_query_params, navigate_to
from utils.ui_components import apply_theme
from config import PAGE_NAMES, BACKEND_URL

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
        navigate_to(st.session_state["nav_radio"])

    with st.sidebar:
        st.markdown('<p class="tech-label">Platform</p>', unsafe_allow_html=True)
        st.markdown('<p class="brand-font">ITTICKET</p>', unsafe_allow_html=True)
        st.markdown('<p class="tech-label" style="margin-top:-5px;">Resolution Engine</p>', unsafe_allow_html=True)
        st.divider()

        current_page = st.session_state.get("current_page", PAGE_NAMES[0])
        # If accessing ticket detail, it might not be in sidebar list, so default to My Tickets or keep it hidden
        if current_page not in PAGE_NAMES and current_page != "Ticket Detail":
            current_page = PAGE_NAMES[0]
        
        display_page = current_page if current_page in PAGE_NAMES else "My Tickets"
        if "nav_radio" not in st.session_state or st.session_state["nav_radio"] != display_page:
            st.session_state["nav_radio"] = display_page

        st.radio(
            "Navigation",
            PAGE_NAMES,
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

        if st.button("Sign Out", key="sign_out_btn"):
            from utils.session_manager import clear_session
            clear_session()
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
    page_map.get(current, dashboard.render)()

if __name__ == "__main__":
    main()
