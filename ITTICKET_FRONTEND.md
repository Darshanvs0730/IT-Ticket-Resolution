# IT Ticket Resolution Suggestion Engine — Frontend Implementation Spec

## Tech Stack
- Python 3.10+
- Streamlit
- HTML + CSS (for UI polish only — no React, no Vue)
- Plotly (for interactive charts)
- requests (for API calls)
- pandas (for data manipulation)

---

## Project Structure

```
ticket-ai/
├── frontend/
│   ├── app.py                      # Main Streamlit app
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── signin.py               # Sign In page
│   │   ├── signup.py               # Sign Up page
│   │   ├── dashboard.py            # Main dashboard
│   │   ├── create_ticket.py        # Create new ticket
│   │   ├── my_tickets.py           # View user's tickets
│   │   ├── ticket_detail.py        # Single ticket view with AI suggestions
│   │   ├── historical_tickets.py   # View/manage historical tickets (admin)
│   │   └── analytics.py            # Analytics and insights
│   ├── utils/
│   │   ├── api_client.py           # Backend API client
│   │   ├── session_manager.py      # Session state management
│   │   ├── validators.py           # Input validation
│   │   └── ui_components.py        # Reusable UI components
│   ├── config.py                   # Configuration
│   ├── requirements.txt
│   └── README.md
└── logs/
    └── frontend_*.log              # Frontend logs
```

---

## Configuration (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# UI Configuration
APP_TITLE = "IT Ticket Resolution Assistant"
APP_ICON = "🎫"
THEME = "light"

# Pagination
TICKETS_PER_PAGE = 20

# Categories
TICKET_CATEGORIES = ["Hardware", "Software", "Network", "Access", "Other"]
TICKET_PRIORITIES = ["Low", "Medium", "High", "Critical"]
TICKET_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
```

---

## Authentication

### Session State Management (utils/session_manager.py)

```python
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

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("username") is not None and \
           st.session_state.get("access_token") is not None

def clear_session():
    """Clear all session state (sign out)"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
```

### Page: Sign Up (pages/signup.py)

- Fields: Username, Email, Password, Confirm Password
- Client-side validation:
  - All fields required
  - Email must contain @ and valid domain
  - Password minimum 8 characters
  - Password must contain: uppercase, lowercase, number
  - Password must match confirm password
- On submit: POST to `/auth/signup`
- On success: show success message, redirect to Sign In page after 2 seconds
- On error (username/email taken): show specific error message below the form
- On error (validation): show validation errors inline per field
- Link at bottom: "Already have an account? Sign In"
- Never show password in plain text — use `type="password"` input

### Page: Sign In (pages/signin.py)

- Fields: Username, Password
- Client-side validation: both fields required
- On submit: POST to `/auth/signin`
- On success:
  - Store `username`, `user_id`, `access_token` in `st.session_state`
  - Redirect to Dashboard
  - Show welcome message: "Welcome back, {username}!"
- On error (invalid credentials): show error message below the form
- On error (network): show "Cannot connect to backend. Please try again."
- Link at bottom: "Don't have an account? Sign Up"
- "Remember me" checkbox (optional) — stores token in browser local storage
- Never show password in plain text

### Auth State Management

At the very top of `app.py`, before any page routing:

```python
from utils.session_manager import init_session_state, is_authenticated, clear_session

# Initialize session state
init_session_state()

# Check authentication
if not is_authenticated():
    # Show only Sign In or Sign Up pages
    show_auth_pages()
else:
    # Show main application
    show_main_app()
```

### Sign Out

- Sign Out button in sidebar (only shown when authenticated)
- On click:
  - Call POST `/auth/signout` with access token
  - Clear all session state
  - Redirect to Sign In page
  - Show message: "Signed out successfully"

---

## Page Refresh Persistence

Use Streamlit query params to persist the current page across browser refreshes:

```python
# At top of navigation logic — read page from URL first
params = st.query_params
if "page" in params:
    st.session_state["current_page"] = params["page"]
elif "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

# Every navigation click must call this function
def navigate_to(page_name):
    st.session_state["current_page"] = page_name
    st.query_params["page"] = page_name
    st.rerun()
```

- Every sidebar navigation button click must call `navigate_to(page_name)`
- URL bar must reflect current page: `?page=Dashboard`, `?page=My+Tickets`, etc.
- On browser refresh, app loads the page shown in the URL — not always the default page
- Sidebar must highlight the active page after refresh

---

## API Client (utils/api_client.py)

```python
import requests
import streamlit as st
from config import BACKEND_URL, API_TIMEOUT

class APIClient:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.timeout = API_TIMEOUT
    
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
                # Token expired — clear session and redirect to sign in
                clear_session()
                st.error("Session expired. Please sign in again.")
                st.rerun()
            elif e.response.status_code == 403:
                st.error("You don't have permission to perform this action.")
            elif e.response.status_code == 404:
                st.error("Resource not found.")
            else:
                error_data = e.response.json() if e.response.content else {}
                st.error(f"Error: {error_data.get('detail', 'Unknown error')}")
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
        """Sign up new user"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/signup",
                json={"username": username, "email": email, "password": password},
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Signup failed: {str(e)}")
            return None
    
    def signin(self, username, password):
        """Sign in existing user"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/signin",
                json={"username": username, "password": password},
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Sign in failed: {str(e)}")
            return None
    
    def create_ticket(self, title, description, category=None, priority="Medium"):
        """Create new ticket"""
        try:
            response = requests.post(
                f"{self.base_url}/tickets",
                json={
                    "title": title,
                    "description": description,
                    "category": category,
                    "priority": priority
                },
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to create ticket: {str(e)}")
            return None
    
    def get_tickets(self, status=None, category=None, limit=50, offset=0):
        """Get user's tickets"""
        try:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            if category:
                params["category"] = category
            
            response = requests.get(
                f"{self.base_url}/tickets",
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch tickets: {str(e)}")
            return None
    
    def get_ticket(self, ticket_id):
        """Get single ticket with resolutions"""
        try:
            response = requests.get(
                f"{self.base_url}/tickets/{ticket_id}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch ticket: {str(e)}")
            return None
    
    def suggest_resolutions(self, ticket_id):
        """Get AI-generated resolution suggestions"""
        try:
            response = requests.post(
                f"{self.base_url}/tickets/{ticket_id}/suggest",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to generate suggestions: {str(e)}")
            return None
    
    def update_ticket(self, ticket_id, status=None, priority=None, category=None):
        """Update ticket"""
        try:
            data = {}
            if status:
                data["status"] = status
            if priority:
                data["priority"] = priority
            if category:
                data["category"] = category
            
            response = requests.patch(
                f"{self.base_url}/tickets/{ticket_id}",
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to update ticket: {str(e)}")
            return None
    
    def submit_feedback(self, resolution_id, was_helpful):
        """Submit feedback on resolution"""
        try:
            response = requests.post(
                f"{self.base_url}/resolutions/{resolution_id}/feedback",
                json={"was_helpful": was_helpful},
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to submit feedback: {str(e)}")
            return None
    
    def health_check(self):
        """Check backend health"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return self._handle_response(response)
        except Exception:
            return None
```

---

## Pages

### Page 1 — Dashboard (pages/dashboard.py)

- Welcome message: "Welcome, {username}!"
- Backend health check indicator at top:
  - Green badge: "Backend Connected"
  - Red badge: "Backend Offline — Please start the server"
- Summary cards (4 cards in a row):
  - Total Tickets (all statuses)
  - Open Tickets (status = Open)
  - Resolved Tickets (status = Resolved)
  - Avg Resolution Time (in hours)
- Quick actions:
  - Button: "Create New Ticket" → navigate to Create Ticket page
  - Button: "View My Tickets" → navigate to My Tickets page
- Recent tickets table (last 10 tickets):
  - Columns: Ticket ID (truncated), Title, Category, Priority, Status, Created At
  - Click on row → navigate to Ticket Detail page
  - Color-code priority: Critical = red, High = orange, Medium = yellow, Low = green
  - Color-code status: Open = blue, In Progress = yellow, Resolved = green, Closed = gray
- Interactive Plotly chart: Tickets by category (bar chart)
- Interactive Plotly chart: Tickets by status over time (line chart)

### Page 2 — Create Ticket (pages/create_ticket.py)

- Form fields:
  - Title (required, max 200 chars)
  - Description (required, textarea, max 2000 chars)
  - Category (dropdown, optional)
  - Priority (dropdown, default: Medium)
- Client-side validation:
  - Title and description required
  - Character limits enforced
- On submit:
  - Show loading spinner
  - POST to `/tickets`
  - On success:
    - Show success message: "Ticket created successfully!"
    - Automatically navigate to Ticket Detail page to show AI suggestions
  - On error: show error message, keep form data
- "Cancel" button → navigate back to Dashboard

### Page 3 — My Tickets (pages/my_tickets.py)

- Filters (sidebar):
  - Status (multi-select)
  - Category (multi-select)
  - Priority (multi-select)
  - Date range (from/to)
- Search bar: search by title or description
- Sort options: Created Date, Updated Date, Priority, Status
- Pagination: 20 tickets per page
- Tickets table:
  - Columns: Ticket ID, Title, Category, Priority, Status, Created At, Updated At
  - Click on row → navigate to Ticket Detail page
  - Color-code priority and status (same as Dashboard)
- Export button: download filtered tickets as CSV
- Bulk actions (checkboxes):
  - Update status for selected tickets
  - Delete selected tickets (with confirmation)

### Page 4 — Ticket Detail (pages/ticket_detail.py)

- Ticket information card:
  - Title (editable inline)
  - Description (editable inline)
  - Category (dropdown, editable)
  - Priority (dropdown, editable)
  - Status (dropdown, editable)
  - Created At, Updated At, Resolved At (read-only)
- "Save Changes" button (only shown if edits made)
- "Delete Ticket" button (with confirmation dialog)
- AI Resolution Suggestions section:
  - Button: "Get AI Suggestions" (if not already generated)
  - Loading spinner while generating suggestions
  - Show processing time: "Suggestions generated in {time}ms"
  - Display exactly 5 numbered resolution steps:
    - Each step in a card with:
      - Step number (1-5)
      - Resolution text
      - Thumbs up / thumbs down buttons for feedback
      - Feedback count (if available)
  - Color-code feedback: thumbs up = green, thumbs down = red
- Similar Historical Tickets section:
  - Show top 5 similar tickets used for AI suggestions
  - Each ticket card shows:
    - Title
    - Description (truncated)
    - Similarity score (percentage)
    - Resolution text (expandable)
  - Click on historical ticket → expand to show full details
- Activity timeline:
  - Show all status changes, updates, feedback submissions
  - Timestamp for each activity
  - User who performed the action

### Page 5 — Historical Tickets (pages/historical_tickets.py)

- Admin-only page (check user role)
- Add new historical ticket form:
  - Title (required)
  - Description (required)
  - Category (optional)
  - Resolution Text (required, textarea)
  - "Add Historical Ticket" button
- Historical tickets table:
  - Columns: Title, Category, Resolution, Times Matched, Created At
  - Sort by: Times Matched (most used solutions first)
  - Search by title or description
  - Click on row → expand to show full details
- Statistics cards:
  - Total Historical Tickets
  - Most Matched Ticket (title + match count)
  - Avg Similarity Score
  - Last Added (date)
- Export button: download all historical tickets as CSV

### Page 6 — Analytics (pages/analytics.py)

- Time period selector: Last 7 days, Last 30 days, Last 90 days, All time
- Summary cards:
  - Total Tickets Created
  - Avg Resolution Time
  - Resolution Rate (% of tickets resolved)
  - User Satisfaction (% of helpful feedback)
- Interactive Plotly charts:
  - Tickets created over time (line chart)
  - Tickets by category (pie chart)
  - Tickets by priority (bar chart)
  - Tickets by status (stacked bar chart over time)
  - Avg resolution time by category (bar chart)
  - AI suggestion accuracy (% helpful feedback by category)
- Top categories table:
  - Category, Total Tickets, Avg Resolution Time, Resolution Rate
  - Sort by any column
- Resolution effectiveness:
  - Show which AI suggestions get the most positive feedback
  - Identify patterns in successful resolutions

---

## Summary Card Rules (fixes N/A bug)

On every page that shows numeric summary cards:
- Convert all columns to numeric using `pd.to_numeric(col, errors="coerce")` before computing averages or sums
- Use f-strings only — never `"string" + float` concatenation
- If result is NaN after computation, show `0` or `0.0` instead of `N/A`
- Round all displayed averages to 1 decimal place
- Handle division by zero gracefully — show `0.0` instead of error

Example:
```python
# BAD
total_tickets = len(df)
avg_time = df["resolution_time"].mean()
st.metric("Avg Resolution Time", f"{avg_time} hours")  # Can show NaN

# GOOD
total_tickets = len(df) if not df.empty else 0
resolution_times = pd.to_numeric(df["resolution_time"], errors="coerce")
avg_time = resolution_times.mean() if not resolution_times.empty else 0.0
avg_time = 0.0 if pd.isna(avg_time) else avg_time
st.metric("Avg Resolution Time", f"{avg_time:.1f} hours")
```

---

## UI Design Rules

- Clean, minimal, professional design suitable for IT support
- Consistent color scheme:
  - Primary: Blue (#1f77b4)
  - Success: Green (#2ca02c)
  - Warning: Orange (#ff7f0e)
  - Danger: Red (#d62728)
  - Info: Light Blue (#17becf)
- Typography:
  - Page titles: 32px, bold
  - Section headers: 24px, semi-bold
  - Body text: 16px, regular
  - Small text: 14px, regular
- Spacing:
  - Consistent padding and margins
  - Use Streamlit columns for layout
  - Cards with subtle shadows
- Icons:
  - Use emoji icons for visual interest
  - Consistent icon usage across pages
- Responsive layout:
  - Works on desktop and tablet
  - Mobile-friendly (Streamlit handles this)
- Loading states:
  - Show spinners for all API calls
  - Disable buttons while processing
  - Show progress bars for long operations
- Empty states:
  - Show helpful messages when no data
  - Provide action buttons to create data
  - Never show empty tables without explanation

---

## Error Handling Rules (apply to every page)

- Every API call wrapped in try/except
- Network errors (connection refused): "Cannot connect to backend at {url}. Please start the FastAPI server."
- API errors (4xx/5xx): show the HTTP status code and error message from backend
- Empty data: show "No tickets found. Create your first ticket to get started." instead of an empty table
- Never show a raw Python traceback to the user
- Log detailed error info to console for debugging
- Show user-friendly error messages with actionable next steps
- Distinguish between:
  - Network errors (backend offline)
  - Authentication errors (token expired)
  - Authorization errors (insufficient permissions)
  - Validation errors (invalid input)
  - Server errors (backend crash)

---

## Interactive Table Rules (apply to every table page)

- Sort: clicking column headers sorts ascending/descending
- Filter: search/filter input above the table
- All tables must handle empty dataframes gracefully (show message, not error)
- All numeric columns: `pd.to_numeric(errors="coerce")` applied before display
- Pagination for large datasets (20 rows per page)
- Row selection with checkboxes for bulk actions
- Export to CSV button
- Column visibility toggle (hide/show columns)
- Responsive column widths

---

## Accessibility

- All buttons have descriptive labels
- All form inputs have labels
- Color is not the only indicator (use icons + text)
- Keyboard navigation supported (Streamlit default)
- Focus indicators visible
- Error messages associated with form fields
- Alt text for any images (if used)

---

## Performance Optimization

- Cache API responses where appropriate:
  ```python
  @st.cache_data(ttl=60)  # Cache for 60 seconds
  def get_tickets():
      return api_client.get_tickets()
  ```
- Lazy load large datasets (pagination)
- Debounce search inputs (wait for user to stop typing)
- Show loading indicators immediately
- Minimize re-runs with proper session state management
- Use `st.fragment` for partial updates (Streamlit 1.30+)

---

## requirements.txt

```
streamlit==1.30.0
requests==2.31.0
pandas==2.1.3
plotly==5.18.0
python-dotenv==1.0.0
```

---

## Running the Frontend

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (optional)
echo "BACKEND_URL=http://localhost:8000" > .env

# 4. Start Streamlit
streamlit run app.py

# Frontend runs on http://localhost:8501
# Opens automatically in default browser
```

---

## Development Tips

- Use `st.write()` for debugging during development
- Enable Streamlit's debug mode: `streamlit run app.py --logger.level=debug`
- Use browser dev tools to inspect network requests
- Test with backend offline to verify error handling
- Test with invalid tokens to verify auth flow
- Test with empty database to verify empty states
- Test all form validations with invalid inputs
- Test pagination with large datasets
- Test all navigation flows and page refresh behavior

---

## Hackathon Demo Checklist

- [ ] Frontend runs on http://localhost:8501
- [ ] Backend connection indicator shows green
- [ ] Signup/signin flow works smoothly
- [ ] All pages load without errors
- [ ] Ticket creation and AI suggestions work
- [ ] Charts and tables display correctly
- [ ] No NaN or N/A values in summary cards
- [ ] Page refresh maintains current page
- [ ] Error messages are user-friendly
- [ ] UI looks clean and professional
