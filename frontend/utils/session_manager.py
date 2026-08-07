import streamlit as st

def init_session_state():
    """Initialize all session state variables"""
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"
    if "selected_ticket_id" not in st.session_state:
        st.session_state["selected_ticket_id"] = None
    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "signin"

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("username") is not None and \
           st.session_state.get("access_token") is not None

def clear_session():
    """Clear all session state (sign out)"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.query_params.clear()
    init_session_state()

def check_query_params():
    params = st.query_params
    
    if "token" in params and "user" in params:
        if "access_token" not in st.session_state or not st.session_state["access_token"]:
            st.session_state["access_token"] = params["token"]
            st.session_state["username"] = params["user"]
            st.session_state["user_id"] = 1
            if "role" in params:
                st.session_state["role"] = params["role"]
                
    if "page" in params:
        st.session_state["current_page"] = params["page"]
    elif "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name
    st.query_params["page"] = page_name
    st.rerun()

def route_to_ticket(ticket_id):
    st.session_state["selected_ticket_id"] = ticket_id
    navigate_to("Ticket Detail")
