import streamlit as st
import time
from utils.api_client import APIClient
from utils.ui_components import section_header, show_error, show_success, priority_badge, status_badge
from utils.session_manager import navigate_to

def render():
    tkt_id = st.session_state.get("selected_ticket_id")
    if not tkt_id:
        st.warning("No ticket selected.")
        if st.button("Go to My Tickets"): navigate_to("My Tickets")
        return

    api = APIClient()
    tkt = api.get_ticket(tkt_id)

    if not tkt:
        st.error(f"Ticket {tkt_id} could not be loaded.")
        if st.button("Back to Dashboard"): navigate_to("Dashboard")
        return

    section_header(f"Ticket Details: {tkt_id}")
    st.button("← Back to My Tickets", on_click=navigate_to, args=("My Tickets",))
    st.divider()

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"### {tkt.get('title')}")
        st.markdown(f"<div style='margin-top: 10px; margin-bottom: 20px; font-size: 15px; color:#4B5563;'>{tkt.get('description')}</div>", unsafe_allow_html=True)
        
        st.markdown("#### AI Resolution Suggestions")
        if st.button("🤖 Generate AI Suggestions"):
            with st.spinner("Analyzing historical tickets and synthesizing solution..."):
                sugg_res = api.suggest_resolutions(tkt_id)
                if sugg_res:
                    st.success(f"Suggestions generated in {sugg_res.get('time_ms', 0)}ms!")
                    st.session_state[f"sugg_{tkt_id}"] = sugg_res.get("suggestions", [])

        suggestions = st.session_state.get(f"sugg_{tkt_id}")
        if suggestions:
            for s in suggestions:
                with st.container(border=True):
                    sc1, sc2 = st.columns([5, 1])
                    with sc1:
                        st.markdown(f"**Step {s['step']}:** {s['text']}")
                    with sc2:
                        # Feedback simulation
                        fb_state = s.get('helpful')
                        bg = "#FFFFFF"
                        if fb_state is True: bg = "#D1FAE5"
                        elif fb_state is False: bg = "#FEE2E2"
                        st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px; text-align:center;'>Feedback Tracked</div>", unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            st.markdown("**Ticket Meta**")
            st.markdown(f"**Status:** <br>{status_badge(tkt.get('status', 'Open'))}", unsafe_allow_html=True)
            st.markdown(f"<br>**Priority:** <br>{priority_badge(tkt.get('priority', 'Medium'))}", unsafe_allow_html=True)
            st.markdown(f"<br>**Category:** {tkt.get('category')}", unsafe_allow_html=True)
            st.markdown(f"**Created:** {tkt.get('created_at')}")
            st.markdown(f"**Updated:** {tkt.get('updated_at')}")
            
            st.divider()
            new_stat = st.selectbox("Update Status", ["Open", "In Progress", "Resolved", "Closed"], index=["Open", "In Progress", "Resolved", "Closed"].index(tkt.get('status', 'Open')))
            if st.button("Save Changes", use_container_width=True):
                if api.update_ticket(tkt_id, status=new_stat):
                    show_success("Status updated!")
                    time.sleep(1)
                    st.rerun()

            st.divider()
            if st.button("Delete Ticket", type="primary", use_container_width=True):
                # Basic confirmation implementation for hackathon MVP
                api.delete_ticket(tkt_id)
                show_success("Deleted!")
                time.sleep(1)
                navigate_to("My Tickets")
