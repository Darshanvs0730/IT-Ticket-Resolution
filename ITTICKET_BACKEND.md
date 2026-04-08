# IT Ticket Resolution Suggestion Engine — Backend Implementation Spec

## Tech Stack
- Python 3.10+
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL (NeonDB) or SQLite (local fallback)
- Scikit-Learn (TF-IDF + Cosine Similarity)
- Groq API (LLaMA 3.1 8B Model)
- bcrypt (for auth password hashing)
- uvicorn
- pytest (comprehensive unit tests)
- python-dotenv (environment variable management)

---

## Project Structure

```
ticket-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app + routes
│   │   ├── models.py               # SQLAlchemy models
│   │   ├── database.py             # Database connection + session
│   │   ├── auth.py                 # Authentication logic
│   │   ├── nlp_engine.py           # TF-IDF + Cosine Similarity
│   │   ├── llm_engine.py           # Groq API integration
│   │   ├── schemas.py              # Pydantic models
│   │   └── utils/
│   │       ├── error_handler.py    # Centralized error handling
│   │       ├── validators.py       # Input validation utilities
│   │       └── security.py         # Security utilities
│   ├── tests/
│   │   ├── test_auth.py            # Authentication tests
│   │   ├── test_nlp_engine.py      # NLP engine tests
│   │   ├── test_llm_engine.py      # LLM integration tests
│   │   ├── test_tickets.py         # Ticket CRUD tests
│   │   └── test_api.py             # API endpoint tests
│   ├── seed_db.py                  # Database seeding script
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   └── (see ITTICKET_FRONTEND.md)
└── logs/
    └── itticket_*.log              # Daily rotating log files
```

---

## Environment Variables (.env)

Create a `.env` file in the `backend/` directory (optional for hackathon):

```env
# Database Configuration
DATABASE_URL=sqlite:///./tickets.db

# Security
SECRET_KEY=hackathon-demo-secret-key-2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Groq API
GROQ_API_KEY=gsk_your_api_key_here

# Application
DEBUG=True
LOG_LEVEL=INFO
```

### Environment Variable Rules
- For hackathon demo, hardcoded fallback values are acceptable
- If `.env` not found, use defaults: SQLite database, demo Groq API key
- Show warning log if using fallback values

---

## Database Models (app/models.py)

### User Model (Authentication — NEVER DROPPED)
```python
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # bcrypt hash ONLY
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tickets = relationship("Ticket", back_populates="user")
```

### Ticket Model
```python
class Ticket(Base):
    __tablename__ = "tickets"
    
    ticket_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # Hardware, Software, Network, Access, Other
    priority = Column(String, default="Medium")  # Low, Medium, High, Critical
    status = Column(String, default="Open")  # Open, In Progress, Resolved, Closed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tickets")
    resolutions = relationship("Resolution", back_populates="ticket", cascade="all, delete-orphan")
```

### Historical Ticket Model (for NLP training)
```python
class HistoricalTicket(Base):
    __tablename__ = "historical_tickets"
    
    historical_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    resolution_text = Column(Text, nullable=False)  # The actual solution that worked
    resolved_at = Column(DateTime, nullable=False)
    similarity_score = Column(Float, nullable=True)  # For tracking match quality
    times_matched = Column(Integer, default=0)  # Track how often this solution is suggested
```

### Resolution Model (AI-generated suggestions)
```python
class Resolution(Base):
    __tablename__ = "resolutions"
    
    resolution_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"), nullable=False)
    suggestion_text = Column(Text, nullable=False)  # One of the 5 AI-generated points
    order = Column(Integer, nullable=False)  # 1-5 for display order
    was_helpful = Column(Boolean, nullable=True)  # User feedback
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="resolutions")
```

---

## Error Handling

### Custom Exception Hierarchy (app/utils/error_handler.py)

```python
class ITTicketError(Exception):
    """Base exception for IT Ticket system"""
    pass

class DatabaseError(ITTicketError):
    """Database connection, query, or constraint errors"""
    pass

class AuthenticationError(ITTicketError):
    """Authentication and authorization failures"""
    pass

class ValidationError(ITTicketError):
    """Input validation failures"""
    pass

class NLPEngineError(ITTicketError):
    """NLP processing errors"""
    pass

class LLMEngineError(ITTicketError):
    """LLM API errors (Groq)"""
    pass

class RateLimitError(ITTicketError):
    """API rate limit exceeded"""
    pass
```

### Features
- Daily rotating logs saved to `logs/itticket_YYYYMMDD.log`
- `@handle_exceptions` decorator for consistent error handling
- `@retry_on_error` decorator for transient failures (API calls, DB connections)
- All API endpoints return proper HTTP status codes with error messages
- Graceful degradation: if LLM fails, return NLP matches only with a warning
- Never expose internal error details to frontend — log them server-side only

---

## NLP Engine (app/nlp_engine.py)

### TF-IDF + Cosine Similarity Implementation

```python
class NLPEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),  # unigrams and bigrams
            min_df=1,
            max_df=0.8
        )
        self.historical_vectors = None
        self.historical_tickets = []
    
    def train(self, historical_tickets: List[HistoricalTicket]):
        """Train TF-IDF model on historical ticket descriptions"""
        # Combine title + description for better matching
        corpus = [f"{t.title} {t.description}" for t in historical_tickets]
        self.historical_vectors = self.vectorizer.fit_transform(corpus)
        self.historical_tickets = historical_tickets
    
    def find_similar_tickets(self, query: str, top_k: int = 5) -> List[Tuple[HistoricalTicket, float]]:
        """Find top K most similar historical tickets using cosine similarity"""
        if self.historical_vectors is None:
            raise NLPEngineError("NLP engine not trained. Run train() first.")
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.historical_vectors).flatten()
        
        # Get top K indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append((self.historical_tickets[idx], float(similarities[idx])))
        
        return results
```

### NLP Engine Rules
- Retrain the model whenever new historical tickets are added
- Cache the trained model in memory for fast lookups
- Minimum similarity threshold: 0.1 (configurable)
- Return empty list if no matches above threshold
- Handle empty corpus gracefully — return error message, don't crash

---

## LLM Engine (app/llm_engine.py)

### Groq API Integration

```python
class LLMEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "llama-3.1-8b-instant"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    @retry_on_error(max_retries=3, backoff=2.0)
    def generate_resolutions(
        self, 
        ticket_description: str, 
        similar_tickets: List[Tuple[HistoricalTicket, float]]
    ) -> List[str]:
        """Generate exactly 5 actionable resolution points using Groq LLM"""
        
        # Build context from similar tickets
        context = self._build_context(similar_tickets)
        
        prompt = f"""You are an IT support expert. Based on the following ticket and similar historical cases, provide EXACTLY 5 clear, actionable resolution steps.

Current Ticket:
{ticket_description}

Similar Historical Cases:
{context}

Requirements:
- Provide EXACTLY 5 numbered resolution steps
- Each step must be specific and actionable
- Steps should be ordered from most likely to resolve the issue to least likely
- Keep each step concise (1-2 sentences)
- Focus on practical solutions, not theory

Format your response as:
1. [First resolution step]
2. [Second resolution step]
3. [Third resolution step]
4. [Fourth resolution step]
5. [Fifth resolution step]
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            resolutions = self._parse_resolutions(content)
            
            # Ensure exactly 5 resolutions
            if len(resolutions) != 5:
                raise LLMEngineError(f"Expected 5 resolutions, got {len(resolutions)}")
            
            return resolutions
            
        except requests.exceptions.Timeout:
            raise LLMEngineError("Groq API request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Groq API rate limit exceeded")
            raise LLMEngineError(f"Groq API error: {e.response.status_code}")
        except Exception as e:
            raise LLMEngineError(f"Unexpected error: {str(e)}")
    
    def _build_context(self, similar_tickets: List[Tuple[HistoricalTicket, float]]) -> str:
        """Build context string from similar tickets"""
        context_parts = []
        for ticket, score in similar_tickets:
            context_parts.append(
                f"- Issue: {ticket.title}\n"
                f"  Description: {ticket.description}\n"
                f"  Resolution: {ticket.resolution_text}\n"
                f"  Similarity: {score:.2f}\n"
            )
        return "\n".join(context_parts)
    
    def _parse_resolutions(self, content: str) -> List[str]:
        """Parse LLM response into list of 5 resolutions"""
        lines = content.strip().split("\n")
        resolutions = []
        
        for line in lines:
            line = line.strip()
            # Match numbered lines: "1. ", "1) ", "1 - ", etc.
            if re.match(r"^\d+[\.\)\-\:]\s+", line):
                resolution = re.sub(r"^\d+[\.\)\-\:]\s+", "", line)
                resolutions.append(resolution)
        
        return resolutions
```

### LLM Engine Rules
- Always retry on transient failures (timeout, 5xx errors)
- Handle rate limits gracefully — return cached results or NLP-only results
- Validate LLM output — must return exactly 5 resolutions
- If LLM fails after retries, fall back to showing only NLP matches with a warning
- Log all LLM requests and responses for debugging
- Never expose API key in logs or error messages

---

## FastAPI Routes (app/main.py)

### Authentication Endpoints

**POST /auth/signup**
```python
Request Body:
{
    "username": "string",
    "email": "string",
    "password": "string"
}

Response (201):
{
    "status": "success",
    "user_id": "uuid",
    "username": "string"
}

Errors:
- 400: Username or email already exists
- 422: Validation error (invalid email format, weak password)
```

**POST /auth/signin**
```python
Request Body:
{
    "username": "string",
    "password": "string"
}

Response (200):
{
    "status": "success",
    "user_id": "uuid",
    "username": "string",
    "access_token": "jwt_token",
    "token_type": "bearer"
}

Errors:
- 401: Invalid credentials
- 422: Validation error
```

**POST /auth/signout**
```python
Headers:
Authorization: Bearer <token>

Response (200):
{
    "status": "success",
    "message": "Signed out successfully"
}
```

### Ticket Endpoints

**POST /tickets**
```python
Headers:
Authorization: Bearer <token>

Request Body:
{
    "title": "string",
    "description": "string",
    "category": "string (optional)",
    "priority": "string (optional, default: Medium)"
}

Response (201):
{
    "status": "success",
    "ticket_id": "uuid",
    "ticket": { ... }
}

Errors:
- 401: Unauthorized
- 422: Validation error (title/description required)
```

**GET /tickets**
```python
Headers:
Authorization: Bearer <token>

Query Params:
- status: string (optional) — filter by status
- category: string (optional) — filter by category
- limit: int (optional, default: 50)
- offset: int (optional, default: 0)

Response (200):
{
    "status": "success",
    "tickets": [ ... ],
    "total": int,
    "limit": int,
    "offset": int
}

Errors:
- 401: Unauthorized
```

**GET /tickets/{ticket_id}**
```python
Headers:
Authorization: Bearer <token>

Response (200):
{
    "status": "success",
    "ticket": { ... },
    "resolutions": [ ... ]
}

Errors:
- 401: Unauthorized
- 404: Ticket not found
```

**PATCH /tickets/{ticket_id}**
```python
Headers:
Authorization: Bearer <token>

Request Body (all fields optional):
{
    "status": "string",
    "priority": "string",
    "category": "string"
}

Response (200):
{
    "status": "success",
    "ticket": { ... }
}

Errors:
- 401: Unauthorized
- 404: Ticket not found
- 403: Forbidden (not ticket owner)
```

**DELETE /tickets/{ticket_id}**
```python
Headers:
Authorization: Bearer <token>

Response (200):
{
    "status": "success",
    "message": "Ticket deleted successfully"
}

Errors:
- 401: Unauthorized
- 404: Ticket not found
- 403: Forbidden (not ticket owner)
```

### Resolution Suggestion Endpoint

**POST /tickets/{ticket_id}/suggest**
```python
Headers:
Authorization: Bearer <token>

Response (200):
{
    "status": "success",
    "ticket_id": "uuid",
    "resolutions": [
        {
            "resolution_id": "uuid",
            "suggestion_text": "string",
            "order": 1
        },
        ... (exactly 5 resolutions)
    ],
    "similar_tickets": [
        {
            "historical_id": "uuid",
            "title": "string",
            "similarity_score": float
        },
        ...
    ],
    "processing_time_ms": int
}

Errors:
- 401: Unauthorized
- 404: Ticket not found
- 500: NLP or LLM engine error (with fallback to NLP-only results)
```

### Resolution Feedback Endpoint

**POST /resolutions/{resolution_id}/feedback**
```python
Headers:
Authorization: Bearer <token>

Request Body:
{
    "was_helpful": boolean
}

Response (200):
{
    "status": "success",
    "message": "Feedback recorded"
}

Errors:
- 401: Unauthorized
- 404: Resolution not found
```

### Historical Tickets Endpoints (Admin Only)

**POST /historical-tickets**
```python
Headers:
Authorization: Bearer <token>

Request Body:
{
    "title": "string",
    "description": "string",
    "category": "string (optional)",
    "resolution_text": "string"
}

Response (201):
{
    "status": "success",
    "historical_id": "uuid"
}

Errors:
- 401: Unauthorized
- 403: Forbidden (admin only)
```

**GET /historical-tickets**
```python
Headers:
Authorization: Bearer <token>

Response (200):
{
    "status": "success",
    "historical_tickets": [ ... ],
    "total": int
}

Errors:
- 401: Unauthorized
```

### Health Check Endpoint

**GET /health**
```python
Response (200):
{
    "status": "healthy",
    "database": "connected",
    "nlp_engine": "ready",
    "llm_engine": "ready",
    "timestamp": "ISO8601"
}
```

---

## NaN Safety Rule

ALL data endpoints must replace NaN / None / null with appropriate defaults before returning JSON:
- Strings: `""` (empty string)
- Numbers: `0` or `0.0`
- Booleans: `false`
- Dates: `null` (acceptable for optional date fields)

Use Pydantic models with proper defaults to enforce this automatically.

---

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Security Best Practices

### Password Security
- Minimum length: 8 characters
- Must contain: uppercase, lowercase, number
- Hash with bcrypt (cost factor: 12)
- Never log or return password hashes

### JWT Tokens
- Use HS256 algorithm
- Expire after 30 minutes (configurable)
- Include user_id and username in payload
- Validate on every protected endpoint

### Input Validation
- Sanitize all user inputs
- Validate email format
- Prevent SQL injection (use SQLAlchemy ORM, never raw SQL)
- Prevent XSS (escape HTML in ticket descriptions)
- Rate limiting on auth endpoints (max 5 attempts per minute)

### API Key Security
- Never commit API keys to version control
- Use environment variables only
- Rotate keys regularly
- Log API usage for monitoring

---

## Database Seeding (seed_db.py)

```python
# Seed ~50 synthetic historical tickets for NLP training
# Categories: Hardware, Software, Network, Access, Other
# Each ticket has: title, description, category, resolution_text

# Example tickets:
# - "Laptop won't turn on" → "Check power adapter connection..."
# - "Can't access shared drive" → "Verify network permissions..."
# - "Printer not responding" → "Restart print spooler service..."
# - "Email not syncing" → "Reconfigure email client settings..."
# - "VPN connection failed" → "Update VPN client to latest version..."
```

Run seeding:
```bash
cd backend
python seed_db.py
```

---

## Testing (Optional for Hackathon)

Basic manual testing is sufficient for hackathon demo:
- Test signup/signin flow
- Test ticket creation
- Test AI suggestion generation
- Test feedback submission

---

## requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
python-dotenv==1.0.0
bcrypt==4.1.1
pyjwt==2.8.0
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.3
requests==2.31.0
```

---

## Running the Backend

```bash
# 1. Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (copy from .env.example and fill in values)
cp .env.example .env

# 4. Seed the database
python seed_db.py

# 5. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Backend runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Hackathon Demo Checklist

- [ ] Backend runs on http://localhost:8000
- [ ] Database seeded with ~50 historical tickets
- [ ] Signup/signin works
- [ ] Ticket creation works
- [ ] AI suggestions generate exactly 5 resolutions
- [ ] Feedback buttons work
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] All endpoints return proper JSON (no NaN values)
- [ ] Error messages are user-friendly
