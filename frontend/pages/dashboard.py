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
        
        # Calculate resolution_time safely
        if "resolution_time" not in df.columns:
            if "resolved_at" in df.columns and "created_at" in df.columns:
                df["resolution_time"] = (pd.to_datetime(df["resolved_at"]) - pd.to_datetime(df["created_at"])).dt.total_seconds() / 3600
            else:
                df["resolution_time"] = float("nan")
                
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
        display_df = recent_df[["ticket_id", "title", "category", "priority", "status", "created_at"]].copy()
        
        # Format created_at
        if "created_at" in display_df.columns:
            display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime('%b %d, %Y %I:%M %p')
            
        
        def format_tkt_id(uid: str):
            return f"TKT-{str(uid)[:8].upper()}" if len(str(uid)) > 8 else str(uid)
            
        display_df["ticket_id"] = display_df["ticket_id"].apply(format_tkt_id)
        
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
            st.markdown("<h5 style='text-align: center; color: #111827; padding-bottom: 10px;'>Tickets by Category</h5>", unsafe_allow_html=True)
            cat_df = df.groupby('category').size().reset_index(name='count')
            fig1 = px.pie(cat_df, names="category", values="count", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            fig1.update_layout(
                plot_bgcolor='#FFFFFF', 
                paper_bgcolor='#FFFFFF', 
                font=dict(color='#111827'),
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig1, use_container_width=True, theme=None)
            
        with cc2:
            st.markdown("<h5 style='text-align: center; color: #111827; padding-bottom: 10px;'>Tickets by Status Over Time</h5>", unsafe_allow_html=True)
            status_time = df.copy()
            status_time["date"] = pd.to_datetime(status_time["created_at"]).dt.date
            status_grouped = status_time.groupby(["date", "status"]).size().reset_index(name="count")
            
            fig2 = px.bar(status_grouped, x="date", y="count", color="status", barmode="group", color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_layout(
                plot_bgcolor='#FFFFFF', 
                paper_bgcolor='#FFFFFF', 
                font=dict(color='#111827'), 
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, title=None)
            )
            fig2.update_xaxes(title_text="", showgrid=False, linecolor="#E5E7EB", tickfont=dict(color='#111827'))
            fig2.update_yaxes(title_text="", showgrid=True, gridcolor="#E5E7EB", zeroline=False, dtick=1, tickfont=dict(color='#111827'))
            st.plotly_chart(fig2, use_container_width=True, theme=None)
