import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from config import BACKEND_URL, API_TIMEOUT
from utils.session_manager import clear_session

# Simple Mock Data 
MOCK_TICKETS = [
    {
        "ticket_id": f"TKT-{random.randint(1000, 9999)}",
        "title": "Cannot access VPN from home",
        "category": "Network",
        "priority": "High",
        "status": "Open",
        "created_at": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_time": "",
        "description": "I get an error 809 when trying to establish the VPN connection. Internet works fine otherwise."
    },
    {
        "ticket_id": f"TKT-{random.randint(1000, 9999)}",
        "title": "Laptop battery draining fast",
        "category": "Hardware",
        "priority": "Medium",
        "status": "In Progress",
        "created_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_time": "",
        "description": "My laptop dies within 1 hour of being unplugged."
    },
    {
        "ticket_id": f"TKT-{random.randint(1000, 9999)}",
        "title": "Request for Adobe Acrobat Pro",
        "category": "Software",
        "priority": "Low",
        "status": "Resolved",
        "created_at": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_time": "24.5",
        "description": "I need Adobe Acrobat Pro to edit some contract PDFs."
    },
    {
        "ticket_id": f"TKT-{random.randint(1000, 9999)}",
        "title": "Outlook not syncing",
        "category": "Software",
        "priority": "Medium",
        "status": "Open",
        "created_at": (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_time": "",
        "description": "It says disconnected at the bottom."
    },
    {
        "ticket_id": f"TKT-{random.randint(1000, 9999)}",
        "title": "Reset password for Workday",
        "category": "Access",
        "priority": "Critical",
        "status": "Resolved",
        "created_at": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_time": "2.1",
        "description": "I am locked out of Workday. Need it to approve timesheets."
    }
]

MOCK_SUGGESTIONS = [
    {"step": 1, "text": "Verify VPN server address is correct.", "helpful": None},
    {"step": 2, "text": "Check if Windows Firewall is blocking IPsec traffic.", "helpful": True},
    {"step": 3, "text": "Restart the IKE and AuthIP IPsec Keying Modules service.", "helpful": None},
    {"step": 4, "text": "Add a new VPN connection manually.", "helpful": False},
    {"step": 5, "text": "Try connecting using a different internet connection (like a mobile hotspot).", "helpful": None}
]

class APIClient:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.timeout = API_TIMEOUT
        self.is_mock = True # Defaults to True if backend is down on init
        self._check_health()
    
    def _check_health(self):
        try:
            res = requests.get(f"{self.base_url}/health", timeout=2)
            if res.status_code == 200:
                self.is_mock = False
        except Exception:
            self.is_mock = True

    def _get_headers(self):
        """Get headers with auth token"""
        token = st.session_state.get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def _handle_response(self, response):
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                if "signin" in response.url or "signup" in response.url:
                    return None
                # Token expired — clear session and redirect to sign in
                from utils.session_manager import clear_session
                clear_session()
                st.error("Session expired. Please sign in again.")
                st.rerun()
            elif e.response.status_code == 403:
                st.error("You don't have permission to perform this action.")
            elif e.response.status_code == 404:
                st.error("Resource not found.")
            else:
                try:
                    error_data = e.response.json() if e.response.content else {}
                    st.error(f"Error: {error_data.get('detail', 'Unknown error')}")
                except Exception:
                    st.error(f"HTTP Error {e.response.status_code}")
            return None
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to backend at {self.base_url}. Is the server running?")
            return None
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None

    def signup(self, username, email, password):
        if self.is_mock:
            return {"access_token": "mock_token_abc123", "user_id": 1, "username": username}
        try:
            response = requests.post(f"{self.base_url}/auth/signup", json={"username": username, "email": email, "password": password}, timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Signup failed: {str(e)}")
            return None

    def signin(self, username, password):
        if self.is_mock:
            if username and password:
                return {"access_token": "mock_token_abc123", "user_id": 1, "username": username}
            return None
        try:
            response = requests.post(f"{self.base_url}/auth/signin", json={"username": username, "password": password}, timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Sign in failed: {str(e)}")
            return None

    def create_ticket(self, title, description, category=None, priority="Medium"):
        if self.is_mock:
            new_ticket = {
                "ticket_id": f"TKT-{random.randint(1000, 9999)}", "title": title, "category": category or "Other", "priority": priority,
                "status": "Open", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "resolution_time": "", "description": description
            }
            MOCK_TICKETS.insert(0, new_ticket)
            return new_ticket
        try:
            response = requests.post(f"{self.base_url}/tickets", json={"title": title, "description": description, "category": category, "priority": priority}, headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to create ticket: {str(e)}")
            return None

    def get_tickets(self, status=None, category=None, limit=50, offset=0):
        if self.is_mock:
            return {"tickets": MOCK_TICKETS, "total": len(MOCK_TICKETS)}
        try:
            params = {"limit": limit, "offset": offset}
            if status: params["status"] = status
            if category: params["category"] = category
            response = requests.get(f"{self.base_url}/tickets", params=params, headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch tickets: {str(e)}")
            return None

    def get_ticket(self, ticket_id):
        if self.is_mock:
            tkt = next((t for t in MOCK_TICKETS if t["ticket_id"] == ticket_id), None)
            if tkt:
                return tkt
            else:
                st.error("Ticket not found.")
                return None
        try:
            response = requests.get(f"{self.base_url}/tickets/{ticket_id}", headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch ticket: {str(e)}")
            return None

    def suggest_resolutions(self, ticket_id):
        if self.is_mock:
            return {"suggestions": MOCK_SUGGESTIONS, "time_ms": random.randint(150, 450)}
        try:
            response = requests.post(f"{self.base_url}/tickets/{ticket_id}/suggest", headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to generate suggestions: {str(e)}")
            return None

    def submit_feedback(self, resolution_id, was_helpful):
        if self.is_mock:
            return {"success": True}
        try:
            response = requests.post(f"{self.base_url}/resolutions/{resolution_id}/feedback", json={"was_helpful": was_helpful}, headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to submit feedback: {str(e)}")
            return None

    def get_historical_tickets(self):
        if self.is_mock:
            return {"tickets": MOCK_TICKETS}
        try:
            response = requests.get(f"{self.base_url}/historical-tickets", headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception:
            return {"tickets": MOCK_TICKETS} # Fallback to mock for analytics

    def update_ticket(self, ticket_id, status=None, priority=None, category=None):
        if self.is_mock:
            for t in MOCK_TICKETS:
                if t["ticket_id"] == ticket_id:
                    if status: t["status"] = status
                    if priority: t["priority"] = priority
                    if category: t["category"] = category
                    t["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True}
        try:
             data = {}
             if status: data["status"] = status
             if priority: data["priority"] = priority
             if category: data["category"] = category
             response = requests.patch(f"{self.base_url}/tickets/{ticket_id}", json=data, headers=self._get_headers(), timeout=self.timeout)
             return self._handle_response(response)
        except Exception as e:
             st.error(f"Failed to update ticket: {str(e)}")
             return None

    def delete_ticket(self, ticket_id):
        if self.is_mock:
            global MOCK_TICKETS
            MOCK_TICKETS = [t for t in MOCK_TICKETS if t["ticket_id"] != ticket_id]
            return {"success": True}
        try:
            response = requests.delete(f"{self.base_url}/tickets/{ticket_id}", headers=self._get_headers(), timeout=self.timeout)
            return self._handle_response(response)
        except Exception as e:
             st.error(f"Failed to delete ticket: {str(e)}")
             return None
