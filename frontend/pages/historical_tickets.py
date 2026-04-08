import streamlit as st
import pandas as pd
from utils.api_client import APIClient
from utils.ui_components import section_header, metric_card

def render():
    section_header("Historical Tickets", "Admin Panel — Manage and review knowledge base used for AI resolutions.")

    api = APIClient()
    res = api.get_historical_tickets()
    df = pd.DataFrame(res.get("tickets", []))

    if not df.empty:
        total = len(df)
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("Total Reference TKTs", total)
        with c2: metric_card("Avg Similarity Target", "84", "%")
        with c3: metric_card("Last Added", df["created_at"].max().split(" ")[0] if "created_at" in df else "N/A")

        st.divider()
        st.markdown("### Reference Database")
        search = st.text_input("Search Historical Records")
        
        filtered = df.copy()
        if search:
            filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]
        
        display_df = filtered[["id", "title", "category", "resolution_time", "created_at"]]
        st.dataframe(display_df, use_container_width=True)
        
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Export KB to CSV", data=csv, file_name="historical_tickets.csv", mime="text/csv")
    else:
        st.info("No historical data available. The AI engine is running in cold-start mode.")
