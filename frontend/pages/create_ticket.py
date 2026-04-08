import streamlit as st
from utils.api_client import APIClient
from utils.ui_components import section_header, show_error, show_success
from utils.session_manager import navigate_to, route_to_ticket
from config import TICKET_CATEGORIES, TICKET_PRIORITIES

def render():
    section_header("Create New Ticket", "Submit a new request to the IT Support team.")
    st.divider()

    with st.container(border=True):
        title = st.text_input("Title (Required)", max_chars=200, placeholder="Brief summary of the issue")
        description = st.text_area("Description (Required)", max_chars=2000, height=200, placeholder="Detailed description of the issue. Please include steps to reproduce.")
        
        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox("Category", options=["Select a Category..."] + TICKET_CATEGORIES)
        with c2:
            priority = st.selectbox("Priority", options=TICKET_PRIORITIES, index=1) # Default Medium

        c3, c4 = st.columns([1, 1])
        with c3:
            if st.button("Submit Ticket", use_container_width=True):
                if not title.strip() or not description.strip():
                    show_error("Title and Description are required.")
                else:
                    cat_val = category if category != "Select a Category..." else "Other"
                    api = APIClient()
                    with st.spinner("Creating ticket..."):
                        tkt = api.create_ticket(title, description, cat_val, priority)
                        if tkt:
                            show_success("Ticket created successfully!")
                            st.session_state["recent_ticket_created"] = True
                            route_to_ticket(tkt.get("id"))
        with c4:
            if st.button("Cancel", use_container_width=True):
                navigate_to("Dashboard")
