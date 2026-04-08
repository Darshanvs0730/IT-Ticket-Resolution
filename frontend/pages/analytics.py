import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_client import APIClient
from utils.ui_components import section_header, metric_card

def render():
    section_header("Analytics & Reports", "Deep dive into IT support performance metrics.")

    api = APIClient()
    res = api.get_tickets()
    df = pd.DataFrame(res.get("tickets", []))

    if df.empty:
        st.info("No data available for analytics.")
        return

    st.markdown("### Support Performance")
    
    total = len(df)
    res_times = pd.to_numeric(df["resolution_time"].replace("", float("nan")), errors="coerce")
    avg_time = res_times.mean() if not res_times.empty else 0.0
    avg_time = 0.0 if pd.isna(avg_time) else avg_time
    
    resolved_count = len(df[df["status"].str.lower() == "resolved"])
    res_rate = (resolved_count / total * 100) if total > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Volume", total)
    with c2: metric_card("Avg Resolution", f"{avg_time:.1f}", "h")
    with c3: metric_card("Resolution Rate", f"{res_rate:.1f}", "%")
    with c4: metric_card("Positive Feedback", "92.5", "%")

    st.divider()

    ca, cb = st.columns(2)
    with ca:
        fig1 = px.pie(df, names="category", title="Tickets by Category", hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig1, use_container_width=True)
    with cb:
        fig2 = px.bar(df, x="priority", title="Tickets by Priority", color="priority", template="simple_white")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    
    # Time Series
    st.markdown("### Arrival vs Resolution Trends")
    df["date"] = pd.to_datetime(df["created_at"]).dt.date
    daily = df.groupby(["date", "status"]).size().reset_index(name="count")
    fig3 = px.area(daily, x="date", y="count", color="status", title="Daily Status Pipeline", template="simple_white")
    st.plotly_chart(fig3, use_container_width=True)
