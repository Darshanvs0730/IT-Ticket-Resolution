import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_client import APIClient
from utils.ui_components import section_header, metric_card, status_badge, priority_badge
from utils.session_manager import navigate_to, route_to_ticket

def render():
    section_header(f"Welcome, {st.session_state.get('username', 'User')}!")
    
    api = APIClient()
    if api.is_mock:
        st.markdown(
            "<div style='display:inline-block; padding: 4px 10px; border-radius: 4px; background-color: #FEE2E2; color: #991B1B; font-weight: bold; font-size: 12px; margin-bottom: 20px;'>⚠️ Backend Offline — Using Mock Data</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='display:inline-block; padding: 4px 10px; border-radius: 4px; background-color: #D1FAE5; color: #065F46; font-weight: bold; font-size: 12px; margin-bottom: 20px;'>✓ Backend Connected</div>",
            unsafe_allow_html=True
        )
        
    res = api.get_tickets()
    if not res:
        st.info("No tickets found. Create your first ticket to get started.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(res.get("tickets", []))

    st.markdown("### Overview")
    
    # Calculate metrics
    if not df.empty:
        total = len(df)
        open_t = len(df[df["status"].str.lower() == "open"])
        resolved_t = len(df[df["status"].str.lower() == "resolved"])
        
        # Safe averge calc
        res_times = pd.to_numeric(df["resolution_time"].replace("", float("nan")), errors="coerce")
        avg_res = res_times.mean() if not res_times.empty else 0.0
        avg_res = 0.0 if pd.isna(avg_res) else avg_res
    else:
        total, open_t, resolved_t, avg_res = 0, 0, 0, 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Tickets", total)
    with c2: metric_card("Open Tickets", open_t)
    with c3: metric_card("Resolved Tickets", resolved_t)
    with c4: metric_card("Avg Resolution", f"{avg_res:.1f}", "h")

    st.divider()

    ca, cb = st.columns(2)
    with ca:
        if st.button("Create New Ticket", use_container_width=True): navigate_to("Create Ticket")
    with cb:
        if st.button("View My Tickets", use_container_width=True): navigate_to("My Tickets")

    st.divider()

    st.markdown("### Recent Activity")
    if not df.empty:
        recent_df = df.head(10).copy()
        display_df = recent_df[["id", "title", "category", "priority", "status", "created_at"]].copy()
        
        # Map statuses & priorities to HTML
        display_df["priority"] = display_df["priority"].apply(priority_badge)
        display_df["status"] = display_df["status"].apply(status_badge)
        
        st.write(
            display_df.to_html(escape=False, index=False, classes=['table', 'table-hover'], border=0),
            unsafe_allow_html=True
        )
        # Note: We aren't doing direct row click here as raw HTML tables don't support it natively in Streamlit
        # But we added "View My Tickets" button for interactability.
    else:
        st.info("No tickets available for recent activity.")

    st.divider()
    st.markdown("### Insights")
    if not df.empty:
        cc1, cc2 = st.columns(2)
        with cc1:
            fig1 = px.bar(df, x="category", title="Tickets by Category", template="simple_white", color_discrete_sequence=['#34ACED'])
            st.plotly_chart(fig1, use_container_width=True)
            
        with cc2:
            status_time = df.groupby(["created_at", "status"]).size().reset_index(name="count")
            status_time["created_at"] = pd.to_datetime(status_time["created_at"]).dt.date
            status_grouped = status_time.groupby(["created_at", "status"])["count"].sum().reset_index()
            fig2 = px.line(status_grouped, x="created_at", y="count", color="status", title="Tickets by Status Over Time", template="simple_white")
            st.plotly_chart(fig2, use_container_width=True)
