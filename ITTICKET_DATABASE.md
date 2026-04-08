# IT Ticket Resolution Suggestion Engine — Database Implementation Spec

## Tech Stack
- SQLAlchemy (ORM)
- SQLite (local database - single file, zero config)
- Python built-in sqlite3 module

---

## Database Configuration

### SQLite (Hackathon Setup)
```python
DATABASE_URL = "sqlite:///./tickets.db"
```

### Connection Settings
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLite - single file database
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

---

## Database Schema

### Table: users (Authentication — NEVER DROPPED)

```sql
CREATE TABLE users (
    user_id         VARCHAR(36) PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin        BOOLEAN NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMP NULL
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
```

SQLAlchemy Model:
```python
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
```

Rules:
- This table is **append-only** — never dropped, never truncated
- Persists across all application restarts
- `password_hash` stores bcrypt-hashed password only (NEVER plain text)
- `user_id` is UUID v4 for security (not sequential integers)
- Soft delete via `is_active` flag (never hard delete users)

---

### Table: tickets

```sql
CREATE TABLE tickets (
    ticket_id       VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    category        VARCHAR(50) NULL,
    priority        VARCHAR(20) NOT NULL DEFAULT 'Medium',
    status          VARCHAR(20) NOT NULL DEFAULT 'Open',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TIMESTAMP NULL,
    
    CONSTRAINT fk_tickets_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE,
    
    CONSTRAINT chk_priority CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    CONSTRAINT chk_status CHECK (status IN ('Open', 'In Progress', 'Resolved', 'Closed'))
);

CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX idx_tickets_user_status ON tickets(user_id, status);
```

SQLAlchemy Model:
```python
class Ticket(Base):
    __tablename__ = "tickets"
    
    ticket_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, index=True)
    priority = Column(String(20), nullable=False, default="Medium", index=True)
    status = Column(String(20), nullable=False, default="Open", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tickets")
    resolutions = relationship("Resolution", back_populates="ticket", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("priority IN ('Low', 'Medium', 'High', 'Critical')", name="chk_priority"),
        CheckConstraint("status IN ('Open', 'In Progress', 'Resolved', 'Closed')", name="chk_status"),
    )
```

Rules:
- Cascade delete: when user is deleted, all their tickets are deleted
- `ticket_id` is UUID v4 for security
- `resolved_at` is automatically set when status changes to "Resolved"
- Composite index on `(user_id, status)` for fast filtering
- Title limited to 200 characters, description unlimited

---

### Table: historical_tickets

```sql
CREATE TABLE historical_tickets (
    historical_id   VARCHAR(36) PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    category        VARCHAR(50) NULL,
    resolution_text TEXT NOT NULL,
    resolved_at     TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    similarity_score FLOAT NULL,
    times_matched   INTEGER NOT NULL DEFAULT 0,
    avg_feedback_score FLOAT NULL
);

CREATE INDEX idx_historical_category ON historical_tickets(category);
CREATE INDEX idx_historical_times_matched ON historical_tickets(times_matched DESC);
CREATE INDEX idx_historical_resolved_at ON historical_tickets(resolved_at DESC);
CREATE FULLTEXT INDEX idx_historical_search ON historical_tickets(title, description);  -- PostgreSQL only
```

SQLAlchemy Model:
```python
class HistoricalTicket(Base):
    __tablename__ = "historical_tickets"
    
    historical_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, index=True)
    resolution_text = Column(Text, nullable=False)
    resolved_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    similarity_score = Column(Float, nullable=True)
    times_matched = Column(Integer, default=0, nullable=False, index=True)
    avg_feedback_score = Column(Float, nullable=True)
```

Rules:
- This table is used for NLP training — contains ~50+ synthetic tickets initially
- New historical tickets can be added by admins
- `times_matched` increments every time this ticket is used in AI suggestions
- `avg_feedback_score` tracks how helpful this solution is (0.0 - 1.0)
- Never delete historical tickets — they improve AI accuracy over time
- Full-text search index on title + description for fast similarity matching

---

### Table: resolutions

```sql
CREATE TABLE resolutions (
    resolution_id   VARCHAR(36) PRIMARY KEY,
    ticket_id       VARCHAR(36) NOT NULL,
    suggestion_text TEXT NOT NULL,
    order_num       INTEGER NOT NULL,
    was_helpful     BOOLEAN NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    feedback_at     TIMESTAMP NULL,
    
    CONSTRAINT fk_resolutions_ticket FOREIGN KEY (ticket_id) 
        REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    
    CONSTRAINT chk_order CHECK (order_num BETWEEN 1 AND 5)
);

CREATE INDEX idx_resolutions_ticket_id ON resolutions(ticket_id);
CREATE INDEX idx_resolutions_order ON resolutions(ticket_id, order_num);
CREATE INDEX idx_resolutions_feedback ON resolutions(was_helpful);
```

SQLAlchemy Model:
```python
class Resolution(Base):
    __tablename__ = "resolutions"
    
    resolution_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    suggestion_text = Column(Text, nullable=False)
    order_num = Column(Integer, nullable=False)
    was_helpful = Column(Boolean, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    feedback_at = Column(DateTime, nullable=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="resolutions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("order_num BETWEEN 1 AND 5", name="chk_order"),
    )
```

Rules:
- Cascade delete: when ticket is deleted, all resolutions are deleted
- Exactly 5 resolutions per ticket (order_num: 1-5)
- `was_helpful` is NULL until user provides feedback
- `feedback_at` is set when user submits feedback
- Composite index on `(ticket_id, order_num)` for fast ordered retrieval

---

### Table: nlp_cache (Optional — Performance Optimization)

```sql
CREATE TABLE nlp_cache (
    cache_id        VARCHAR(36) PRIMARY KEY,
    query_hash      VARCHAR(64) UNIQUE NOT NULL,
    query_text      TEXT NOT NULL,
    similar_tickets JSON NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP NOT NULL,
    hit_count       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_nlp_cache_hash ON nlp_cache(query_hash);
CREATE INDEX idx_nlp_cache_expires ON nlp_cache(expires_at);
```

SQLAlchemy Model:
```python
class NLPCache(Base):
    __tablename__ = "nlp_cache"
    
    cache_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    similar_tickets = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0, nullable=False)
```

Rules:
- Cache NLP similarity search results for 1 hour
- `query_hash` is SHA-256 hash of normalized query text
- `similar_tickets` stores JSON array of historical ticket IDs + scores
- Automatically expire old cache entries (cleanup job runs daily)
- `hit_count` tracks cache effectiveness

---

### Table: audit_log (Optional — Security & Compliance)

```sql
CREATE TABLE audit_log (
    log_id          BIGSERIAL PRIMARY KEY,
    user_id         VARCHAR(36) NULL,
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     VARCHAR(36) NULL,
    details         JSON NULL,
    ip_address      VARCHAR(45) NULL,
    user_agent      TEXT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);
```

SQLAlchemy Model:
```python
class AuditLog(Base):
    __tablename__ = "audit_log"
    
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

Rules:
- Log all critical actions: signup, signin, ticket create/update/delete, resolution feedback
- Never delete audit logs — append-only table
- Partition by month for large datasets (PostgreSQL)
- `user_id` can be NULL for anonymous actions (e.g., failed login attempts)
- `details` stores JSON with action-specific metadata

---

## Database Initialization

### Create All Tables (app/database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Ticket, HistoricalTicket, Resolution

def init_db():
    """Initialize database — create all tables"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

def drop_all_tables():
    """Drop all tables — USE WITH CAUTION"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped")

def reset_db():
    """Reset database — drop and recreate all tables"""
    drop_all_tables()
    init_db()
    print("Database reset complete")
```

Run initialization:
```bash
python -c "from app.database import init_db; init_db()"
```

---

## Database Seeding (seed_db.py)

### Seed Historical Tickets (~50 synthetic tickets)

```python
import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import HistoricalTicket

def seed_historical_tickets():
    """Seed database with ~50 synthetic historical tickets"""
    db = SessionLocal()
    
    # Sample tickets by category
    tickets_data = [
        # Hardware
        {
            "title": "Laptop won't turn on",
            "description": "My laptop doesn't power on when I press the power button. The charging light is on.",
            "category": "Hardware",
            "resolution_text": "1. Check power adapter connection\n2. Try a different power outlet\n3. Remove battery and hold power button for 30 seconds\n4. Reconnect battery and try again\n5. If still not working, contact hardware support"
        },
        {
            "title": "Monitor displays no signal",
            "description": "External monitor shows 'No Signal' message even though it's connected to laptop.",
            "category": "Hardware",
            "resolution_text": "1. Check cable connections (HDMI/DisplayPort)\n2. Try a different cable\n3. Press Windows+P and select 'Extend' or 'Duplicate'\n4. Update graphics drivers\n5. Test monitor with another device"
        },
        # Software
        {
            "title": "Application crashes on startup",
            "description": "Microsoft Excel crashes immediately after opening. Error message says 'Excel has stopped working'.",
            "category": "Software",
            "resolution_text": "1. Restart computer\n2. Run Excel in Safe Mode (hold Ctrl while opening)\n3. Disable add-ins in Excel Options\n4. Repair Office installation via Control Panel\n5. Reinstall Microsoft Office"
        },
        {
            "title": "Cannot install software update",
            "description": "Windows Update fails with error code 0x80070002.",
            "category": "Software",
            "resolution_text": "1. Run Windows Update Troubleshooter\n2. Clear Windows Update cache (delete C:\\Windows\\SoftwareDistribution)\n3. Restart Windows Update service\n4. Run 'sfc /scannow' in Command Prompt as admin\n5. Download update manually from Microsoft Update Catalog"
        },
        # Network
        {
            "title": "Cannot connect to WiFi",
            "description": "Laptop doesn't show any available WiFi networks. WiFi icon has a red X.",
            "category": "Network",
            "resolution_text": "1. Toggle WiFi off and on in Settings\n2. Restart computer\n3. Update WiFi adapter driver\n4. Run Network Troubleshooter\n5. Reset network settings (netsh winsock reset)"
        },
        {
            "title": "VPN connection fails",
            "description": "VPN client shows 'Connection failed' error when trying to connect to corporate network.",
            "category": "Network",
            "resolution_text": "1. Check internet connection\n2. Verify VPN credentials\n3. Update VPN client to latest version\n4. Disable firewall temporarily to test\n5. Contact network admin to verify VPN server status"
        },
        # Access
        {
            "title": "Forgot password",
            "description": "I forgot my Windows login password and cannot access my account.",
            "category": "Access",
            "resolution_text": "1. Use password reset link on login screen\n2. Answer security questions\n3. Use alternate email for verification\n4. Contact IT helpdesk with employee ID\n5. Admin will reset password and send temporary credentials"
        },
        {
            "title": "Cannot access shared drive",
            "description": "Getting 'Access Denied' error when trying to open shared network drive.",
            "category": "Access",
            "resolution_text": "1. Verify you have permission to access the drive\n2. Check if you're connected to corporate network/VPN\n3. Re-enter network credentials\n4. Clear cached credentials in Credential Manager\n5. Contact IT to verify your access permissions"
        },
        # Add 42 more similar tickets...
    ]
    
    # Generate resolved_at dates (random dates in past 6 months)
    for ticket_data in tickets_data:
        resolved_at = datetime.utcnow() - timedelta(days=random.randint(1, 180))
        
        ticket = HistoricalTicket(
            title=ticket_data["title"],
            description=ticket_data["description"],
            category=ticket_data["category"],
            resolution_text=ticket_data["resolution_text"],
            resolved_at=resolved_at,
            times_matched=0,
            avg_feedback_score=None
        )
        db.add(ticket)
    
    db.commit()
    print(f"Seeded {len(tickets_data)} historical tickets")
    db.close()

if __name__ == "__main__":
    seed_historical_tickets()
```

Run seeding:
```bash
cd backend
python seed_db.py
```

---

## Database Behavior Rules

### Append-Only Tables (NEVER dropped or truncated)
- `users` — authentication table, persists forever
- `audit_log` — compliance requirement, never delete

### Regular Tables (can be cleared for testing)
- `tickets` — user tickets, can be deleted by user
- `resolutions` — AI suggestions, cascade deleted with tickets
- `historical_tickets` — training data, should not be deleted in production
- `nlp_cache` — performance cache, can be cleared anytime

### Cascade Delete Rules
- Delete user → delete all their tickets → delete all resolutions for those tickets
- Delete ticket → delete all resolutions for that ticket
- Never cascade delete historical tickets

### NULL Handling
- All INSERT operations handle NULL values gracefully
- Required fields (NOT NULL) validated at application layer before INSERT
- Optional fields can be NULL — no default value unless specified
- Never insert empty strings for NULL fields — use actual NULL

### Transaction Management
- All write operations wrapped in transactions
- Rollback on any error
- Use `db.commit()` only after all operations succeed
- Use `db.rollback()` in exception handlers

---

## Indexes and Performance

### Index Strategy
- Primary keys: automatic unique index
- Foreign keys: always indexed for JOIN performance
- Frequently filtered columns: status, category, priority, created_at
- Composite indexes for common query patterns: (user_id, status)
- Full-text search indexes for text search (PostgreSQL only)

### Query Optimization
- Use `EXPLAIN ANALYZE` to profile slow queries
- Add indexes for columns in WHERE, JOIN, ORDER BY clauses
- Avoid SELECT * — specify only needed columns
- Use pagination (LIMIT/OFFSET) for large result sets
- Use connection pooling to reduce connection overhead

### Database Maintenance
- Vacuum PostgreSQL tables weekly (auto-vacuum enabled)
- Analyze tables after bulk inserts
- Monitor index usage and drop unused indexes
- Archive old audit logs (older than 1 year)
- Monitor database size and plan for scaling

---

## Backup (Simple for Hackathon)

### SQLite Backup
```bash
# Backup - just copy the file
cp tickets.db tickets_backup.db

# Restore
cp tickets_backup.db tickets.db
```

---

## Security Best Practices

### Connection Security
- Always use SSL/TLS for PostgreSQL connections (`sslmode=require`)
- Never commit database credentials to version control
- Use environment variables for DATABASE_URL
- Rotate database passwords regularly
- Use read-only database users for analytics queries

### SQL Injection Prevention
- Always use SQLAlchemy ORM — never raw SQL with string concatenation
- Use parameterized queries if raw SQL is necessary
- Validate and sanitize all user inputs
- Use prepared statements

### Data Privacy
- Hash all passwords with bcrypt (never plain text)
- Never log sensitive data (passwords, tokens, PII)
- Implement soft delete for users (set is_active=False)
- Encrypt sensitive fields at application layer if needed
- Comply with GDPR/data retention policies

---

## Database Schema Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ user_id (PK)    │
│ username        │
│ email           │
│ password_hash   │
│ created_at      │
│ is_active       │
│ is_admin        │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│    tickets      │
├─────────────────┤
│ ticket_id (PK)  │
│ user_id (FK)    │
│ title           │
│ description     │
│ category        │
│ priority        │
│ status          │
│ created_at      │
│ resolved_at     │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│  resolutions    │
├─────────────────┤
│ resolution_id   │
│ ticket_id (FK)  │
│ suggestion_text │
│ order_num       │
│ was_helpful     │
│ created_at      │
└─────────────────┘

┌─────────────────────┐
│ historical_tickets  │
├─────────────────────┤
│ historical_id (PK)  │
│ title               │
│ description         │
│ category            │
│ resolution_text     │
│ resolved_at         │
│ times_matched       │
│ avg_feedback_score  │
└─────────────────────┘
```

---

## Testing Database Operations

```python
# Test database connection
def test_db_connection():
    db = SessionLocal()
    try:
        db.execute("SELECT 1")
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
    finally:
        db.close()

# Test user creation
def test_create_user():
    db = SessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$..."
    )
    db.add(user)
    db.commit()
    print(f"User created: {user.user_id}")
    db.close()

# Test ticket creation
def test_create_ticket():
    db = SessionLocal()
    ticket = Ticket(
        user_id="existing-user-id",
        title="Test ticket",
        description="Test description",
        category="Software",
        priority="Medium"
    )
    db.add(ticket)
    db.commit()
    print(f"Ticket created: {ticket.ticket_id}")
    db.close()
```

---

## Hackathon Demo Checklist

- [ ] Database file `tickets.db` created successfully
- [ ] All tables created (users, tickets, historical_tickets, resolutions)
- [ ] Database seeded with ~50 historical tickets
- [ ] Signup creates new user in database
- [ ] Signin validates credentials correctly
- [ ] Tickets are saved and retrieved properly
- [ ] AI resolutions are stored with correct order (1-5)
- [ ] Feedback updates resolution records
- [ ] No database errors in logs
- [ ] Database file size is reasonable (<50MB for demo)
