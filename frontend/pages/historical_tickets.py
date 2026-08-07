import streamlit as st
import pandas as pd
from utils.api_client import APIClient
from utils.ui_components import section_header, metric_card

def render():
    section_header("Historical Tickets", "Admin Panel — Manage and review knowledge base used for AI resolutions.")

    api = APIClient()
    res = api.get_historical_tickets()
    tickets_data = res.get("historical_tickets") or res.get("tickets", [])
    df = pd.DataFrame(tickets_data)

    if not df.empty:
        total = len(df)
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("Total Reference TKTs", total)
        with c2: metric_card("Avg Similarity Target", "84", "%")
        date_col = "created_at" if "created_at" in df else "resolved_at"
        if date_col in df and not df[date_col].isna().all():
            last_added = pd.to_datetime(df[date_col].max()).strftime('%b %d, %Y %I:%M %p')
        else:
            last_added = "N/A"
        with c3: metric_card("Last Added", last_added)

        st.divider()
        st.markdown("### Reference Database")
        search = st.text_input("Search Historical Records")
        
        filtered = df.copy()
        if search:
            filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]
        
        id_col = "historical_id" if "historical_id" in filtered.columns else "ticket_id"
        time_col = "resolution_time" if "resolution_time" in filtered.columns else "resolved_at"
        date_col = "created_at" if "created_at" in filtered.columns else "resolved_at"
        
        # Select available columns safely and remove duplicates
        raw_cols = [id_col, "title", "category", time_col, date_col]
        cols_to_show = list(dict.fromkeys([c for c in raw_cols if c in filtered.columns]))
        display_df = filtered[cols_to_show].copy()
        
        for col in ["created_at", "resolved_at", "resolution_time"]:
            if col in display_df.columns:
                display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%b %d, %Y %I:%M %p')
                
        if "historical_id" in display_df.columns:
            display_df["historical_id"] = display_df["historical_id"].apply(lambda x: f"REF-{str(x)[-8:].upper()}" if pd.notnull(x) else x)
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Export KB to CSV", data=csv, file_name="historical_tickets.csv", mime="text/csv")
    else:
        st.info("No historical data available. The AI engine is running in cold-start mode.")
