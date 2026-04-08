import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

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
