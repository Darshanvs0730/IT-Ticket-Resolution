from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime

class NaNProtectedModel(BaseModel):
    @field_validator('*', mode='before')
    @classmethod
    def replace_nan_or_none(cls, v: Any) -> Any:
        # Check for NaN and null values specifically handling strings and numbers
        if v is None:
            return v  # Will be managed by default values mapped to fields
        if isinstance(v, float) and v != v:
            return 0.0
        return v

# Input Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str

class TicketCreate(BaseModel):
    title: str
    description: str
    category: str = ""
    priority: str = "Medium"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None

class HistoricalTicketCreate(BaseModel):
    title: str
    description: str
    category: str = ""
    resolution_text: str

class ResolutionFeedback(BaseModel):
    was_helpful: bool

# Output Schemas enforces NaN safety naturally
class UserOut(NaNProtectedModel):
    user_id: str = ""
    username: str = ""
    class Config:
        from_attributes = True

class ResolutionOut(NaNProtectedModel):
    resolution_id: str = ""
    suggestion_text: str = ""
    order: int = 0
    was_helpful: Optional[bool] = None
    class Config:
        from_attributes = True

class TicketOut(NaNProtectedModel):
    ticket_id: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    priority: str = ""
    status: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class HistoricalTicketOut(NaNProtectedModel):
    historical_id: str = ""
    title: str = ""
    similarity_score: float = 0.0
    class Config:
        from_attributes = True
        
class HistoricalTicketFullOut(NaNProtectedModel):
    historical_id: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    resolution_text: str = ""
    resolved_at: Optional[datetime] = None
    similarity_score: float = 0.0
    times_matched: int = 0
    class Config:
        from_attributes = True
