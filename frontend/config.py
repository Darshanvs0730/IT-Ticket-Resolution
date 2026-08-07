import os
from dotenv import load_dotenv

load_dotenv()

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# UI Configuration
APP_TITLE = "IT Ticket Resolution Assistant"
APP_ICON = "🎫"
THEME = "light" # Not used since we manually apply CSS overrides

# Pagination
TICKETS_PER_PAGE = 20

# Categories & Statuses
TICKET_CATEGORIES = ["Hardware", "Software", "Network", "Access", "Other"]
TICKET_PRIORITIES = ["Low", "Medium", "High", "Critical"]
TICKET_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

PAGE_NAMES = [
    "Dashboard",
    "Create Ticket",
    "My Tickets",
    "Historical Tickets",
    "Analytics"
]
ADMIN_USERS = ["admin"]
