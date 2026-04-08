# IT Ticket Resolution Suggestion Engine - Database Layer

A production-ready SQLite database implementation for an IT Ticket Resolution system.

## Project Structure
- `database.py`: Python manager for SQLite connections and operations.
- `schema.sql`: Full DDL schema for the database.
- `tickets.db`: (Auto-generated) The SQLite database file.

## Setup
Ensure you have Python installed. You can initialize the database by running:

```bash
python database.py
```

## Features
- **Strict Typing**: PostgreSQL-like CHECK constraints for priorities and status.
- **Data Integrity**: Foreign key constraints enabled via PRAGMAS.
- **Performance**: Pre-configured indexes for frequently queried fields.
- **NLP Readiness**: Includes an `nlp_cache` table for storing model outputs.
- **Audit Tracking**: `audit_log` table ready for tracking record changes.
