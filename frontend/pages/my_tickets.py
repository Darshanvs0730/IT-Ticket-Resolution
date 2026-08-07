import streamlit as st
import pandas as pd
from utils.api_client import APIClient
from utils.ui_components import section_header, status_badge, priority_badge
from utils.session_manager import navigate_to, route_to_ticket
from config import TICKET_CATEGORIES, TICKET_PRIORITIES, TICKET_STATUSES

def render():
    section_header("My Tickets", "View and manage all your submitted tickets.")

    api = APIClient()
    res = api.get_tickets()
    if not res or not res.get("tickets"):
        st.info("No tickets found. Create your first ticket to get started.")
        if st.button("Create New Ticket"): navigate_to("Create Ticket")
        return

    df = pd.DataFrame(res.get("tickets", []))

    with st.expander("Filters & Search", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1: stat_filter = st.multiselect("Status", TICKET_STATUSES)
        with f2: cat_filter = st.multiselect("Category", TICKET_CATEGORIES)
        with f3: search_text = st.text_input("Search (Title/Description)")

    # Apply filters
    filtered_df = df.copy()
    if stat_filter:
        filtered_df = filtered_df[filtered_df["status"].isin(stat_filter)]
    if cat_filter:
        filtered_df = filtered_df[filtered_df["category"].isin(cat_filter)]
    if search_text:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_text, case=False, na=False) |
            filtered_df["description"].str.contains(search_text, case=False, na=False)
        ]

    if filtered_df.empty:
        st.warning("No tickets match the current filters.")
        return

    # Export
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Export to CSV", data=csv, file_name="tickets.csv", mime="text/csv")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    display_df = filtered_df[["ticket_id", "title", "category", "priority", "status", "created_at"]].copy()
    
    # Format created_at to be readable
    if "created_at" in display_df.columns:
        display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime('%b %d, %Y %I:%M %p')
    
    def format_tkt_id(uid: str):
        return f"TKT-{str(uid)[:8].upper()}" if len(str(uid)) > 8 else str(uid)
        
    display_df["ticket_id"] = display_df["ticket_id"].apply(format_tkt_id)

    # Create a nice layout to allow clicking a row and routing to its details
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    tkt_input_id = st.text_input("Enter Ticket ID to View Details (e.g. TKT-F172DDCB)", key="tkt_view_input")
    if st.button("View Ticket Detail"):
        if tkt_input_id:
            input_upper = tkt_input_id.strip().upper()
            matched_row = filtered_df[filtered_df["ticket_id"].apply(format_tkt_id) == input_upper]
            if not matched_row.empty:
                real_id = matched_row.iloc[0]["ticket_id"]
                route_to_ticket(real_id)
            else:
                route_to_ticket(tkt_input_id)
