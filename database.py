import sqlite3
import os
from contextlib import contextmanager

DB_NAME = "tickets.db"
SCHEMA_FILE = "schema.sql"

class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Enables column access by name
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def initialize_db(self, schema_path=SCHEMA_FILE):
        """Creates tables using the schema.sql file."""
        if not os.path.exists(schema_path):
            print(f"Error: Schema file '{schema_path}' not found.")
            return

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        try:
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            print(f"Database '{self.db_name}' initialized successfully.")
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")

    def add_user(self, username, email, role="user"):
        """Inserts a new user into the database."""
        query = "INSERT INTO users (username, email, role) VALUES (?, ?, ?);"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (username, email, role))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"User '{username}' or email '{email}' already exists.")
            return None

    def get_tickets(self):
        """Fetches all tickets from the database."""
        query = "SELECT * FROM tickets;"
        with self.get_connection() as conn:
            return [dict(row) for row in conn.execute(query).fetchall()]

if __name__ == "__main__":
    # Self-initialization and sanity check
    db = DatabaseManager()
    
    # Initialize schema
    db.initialize_db()
    
    # Simple sanity check: Add a test user
    user_id = db.add_user("admin_user", "admin@example.com", "admin")
    if user_id:
        print(f"Verified: Added test user with ID {user_id}")
    
    # Fetch tickets (should be empty but shouldn't error)
    tickets = db.get_tickets()
    print(f"Verified: Ticket count is {len(tickets)}")
