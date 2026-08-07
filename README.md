# IT Ticket Resolution Engine

An AI-powered IT Ticket Resolution system designed to streamline technical support workflows. By utilizing a FastAPI backend and a beautiful Streamlit frontend, the system offers instant, intelligent resolution suggestions to IT tickets using Groq LLM (LLaMA 3) and TF-IDF similarity mapping against historical resolutions.

---

## 🎯 Target Audience (Who is this for?)
This system is highly useful for:
- **IT Support Teams & Help Desks:** Automates repetitive ticket responses and dramatically reduces Mean Time to Resolution (MTTR).
- **System Administrators:** Provides an easy way to manage historical knowledge bases and oversee the ticket queue.
- **Employees / End-Users:** Empowers users with instant AI-driven solutions to common technical problems, potentially solving their issues before human intervention is even required.

## ✨ Key Features
- **Instant AI Resolutions:** Automatically suggests resolutions for newly created tickets by finding similar past issues (TF-IDF) and using LLM generation (LLaMA 3) to synthesize a tailored response.
- **Role-Based Access Control (RBAC):** Seamlessly supports Standard Users (who create and view their own tickets) and Administrators (who can view analytics and manage the historical knowledge base).
- **Interactive Analytics Dashboard:** Real-time visualizations of ticket statuses and categories using Plotly.
- **Historical Knowledge Base (KB):** Administrators can manage a database of past resolutions which the AI uses to train its responses.
- **Export Capabilities:** Easy CSV export functionality for historical records and active ticket queues.
- **Clean, Modern UI:** A highly polished, responsive interface built with Streamlit and custom CSS styling.

## 🚀 Advantages & Benefits
- **Reduces Support Load:** Deflects common Level-1 support tickets by providing instant, accurate self-service solutions.
- **Knowledge Retention:** Prevents "brain drain" by storing institutional knowledge in a queryable historical database.
- **High Performance:** Built on FastAPI, the backend handles concurrent API requests with lightning-fast async operations.
- **Scalable Architecture:** Clean separation of concerns between the backend API and frontend UI allows each to be scaled or replaced independently.

## 🔄 App Flow & User Flow

### 1. Standard User Flow
1. **Authentication:** User signs up / logs in via JWT-secured endpoints.
2. **Dashboard Overview:** User sees a high-level overview of their ticket statistics.
3. **Ticket Creation:** User submits a new IT issue (Title, Category, Priority, Description).
4. **AI Processing:** Upon submission, the engine cross-references the issue with the Historical Database. If a match is found, the AI generates a customized, immediate resolution.
5. **Resolution Review:** User views the suggested AI resolution in their `My Tickets` portal.

### 2. Administrator Flow
1. **Admin Login:** Admin logs in using an authorized admin account (username: `admin`).
2. **Knowledge Base Management:** Admin accesses the `Historical Tickets` portal to view the raw data feeding the AI engine.
3. **System Analytics:** Admin accesses the `Analytics` portal to monitor organization-wide ticket metrics (volume by category, resolution times, etc.).

---

## 🛠️ Tech Stack

**Backend:**
- **Python 3.10+** (Core Language)
- **FastAPI** (High-performance API framework)
- **SQLAlchemy** (ORM for database interactions)
- **SQLite** (Lightweight database for portability)
- **Scikit-Learn** (TF-IDF Vectorization & Cosine Similarity)
- **Groq API / LLaMA 3.1 8B** (LLM for text generation)
- **PyJWT & Passlib** (Authentication and password hashing)
- **Uvicorn** (ASGI server)

**Frontend:**
- **Streamlit** (Rapid UI development)
- **Pandas** (Data manipulation)
- **Plotly** (Interactive charting)
- **Requests** (HTTP client for API communication)

---

## 📂 Project Structure

```
IT-Ticket-Resolution/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI application entry point
│   │   ├── database.py    # SQLite connections and ORM models
│   │   ├── auth.py        # JWT authentication logic
│   │   ├── ai_service.py  # Groq LLM integration and context management
│   │   └── nlp.py         # TF-IDF similarity engine
│   └── seed_db.py         # Script to seed synthetic historical tickets
│
├── frontend/
│   ├── app.py             # Streamlit frontend entry point
│   ├── pages/             # Streamlit application pages (Dashboard, etc.)
│   └── utils/             # API client and UI components
│
├── database.py            # SQLite configuration (legacy root config)
├── schema.sql             # Full DDL schema for the database
└── tickets.db             # Local SQLite database file
```

---

## ⚙️ Setup & Running Locally

Ensure you have Python installed. The project runs in two parts:

### 1. Run the Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
*The backend API will be available at http://localhost:8000*

### 2. Run the Frontend
In a new terminal window:
```bash
cd frontend
python -m streamlit run app.py
```
*The Streamlit web interface will be available at http://localhost:8502*
