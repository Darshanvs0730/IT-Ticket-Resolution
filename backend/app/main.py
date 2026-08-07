import os
import time
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from .database import engine, Base, get_db
from . import models, schemas, auth
from .nlp_engine import NLPEngine
from .llm_engine import LLMEngine
from .utils.error_handler import handle_exceptions, logger

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IT Ticket Resolution Suggestion Engine")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engines
nlp_engine = NLPEngine()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "gsk_your_api_key_here")
llm_engine = LLMEngine(api_key=GROQ_API_KEY)

@app.on_event("startup")
def startup_event():
    # Train NLP engine on startup
    db = next(get_db())
    try:
        historical_tickets = db.query(models.HistoricalTicket).all()
        nlp_engine.train(historical_tickets)
        logger.info(f"NLP Engine trained with {len(historical_tickets)} historical tickets.")
    except Exception as e:
        logger.error(f"Failed to train NLP engine on startup: {str(e)}")
    finally:
        db.close()

# Auth Endpoints
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter((models.User.username == user.username) | (models.User.email == user.email)).first():
        from .utils.error_handler import AuthenticationError
        raise AuthenticationError("Username or email already exists")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"status": "success", "user_id": db_user.user_id, "username": db_user.username}

@app.post("/auth/signin")
@handle_exceptions
async def signin(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        from .utils.error_handler import AuthenticationError
        raise AuthenticationError("Invalid credentials")
        
    access_token = auth.create_access_token(data={"user_id": db_user.user_id, "username": db_user.username})
    return {
        "status": "success", 
        "user_id": db_user.user_id, 
        "username": db_user.username,
        "access_token": access_token, 
        "token_type": "bearer"
    }

@app.post("/auth/signout")
@handle_exceptions
async def signout(current_user: models.User = Depends(auth.get_current_user)):
    return {"status": "success", "message": "Signed out successfully"}

# Ticket Endpoints
@app.post("/tickets", status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def create_ticket(ticket: schemas.TicketCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_ticket = models.Ticket(
        **ticket.model_dump(),
        user_id=current_user.user_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return {"status": "success", "ticket_id": db_ticket.ticket_id, "ticket": schemas.TicketOut.model_validate(db_ticket)}

@app.get("/tickets")
@handle_exceptions
async def get_tickets(
    status: Optional[str] = None, 
    category: Optional[str] = None, 
    limit: int = 50, 
    offset: int = 0, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(models.Ticket)
    query = query.filter(models.Ticket.user_id == current_user.user_id)
    
    if status is not None:
        query = query.filter(models.Ticket.status == status)
    if category is not None:
        query = query.filter(models.Ticket.category == category)
        
    total = query.count()
    tickets = query.offset(offset).limit(limit).all()
    
    return {
        "status": "success",
        "tickets": [schemas.TicketOut.model_validate(t) for t in tickets],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/tickets/{ticket_id}")
@handle_exceptions
async def get_ticket(ticket_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    resolutions = db.query(models.Resolution).filter(models.Resolution.ticket_id == ticket_id).order_by(models.Resolution.order).all()
    
    return {
        "status": "success",
        "ticket": schemas.TicketOut.model_validate(ticket),
        "resolutions": [schemas.ResolutionOut.model_validate(r) for r in resolutions]
    }

@app.patch("/tickets/{ticket_id}")
@handle_exceptions
async def update_ticket(ticket_id: str, ticket_update: schemas.TicketUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if db_ticket.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    update_data = ticket_update.model_dump(exclude_unset=True)
    if not update_data:
        return {"status": "success", "ticket": schemas.TicketOut.model_validate(db_ticket)}

    for key, value in update_data.items():
        setattr(db_ticket, key, value)
    
    if update_data.get('status') == 'Resolved' and not db_ticket.resolved_at:
        db_ticket.resolved_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_ticket)
    
    return {"status": "success", "ticket": schemas.TicketOut.model_validate(db_ticket)}

@app.delete("/tickets/{ticket_id}")
@handle_exceptions
async def delete_ticket(ticket_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if db_ticket.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    db.delete(db_ticket)
    db.commit()
    
    return {"status": "success", "message": "Ticket deleted successfully"}

# Resolution Suggestion
@app.post("/tickets/{ticket_id}/suggest")
@handle_exceptions
async def suggest_resolutions(ticket_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    start_time = time.time()
    db_ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Get similar tickets from NLP
    try:
        query = f"{db_ticket.title} {db_ticket.description}"
        similar_tickets = nlp_engine.find_similar_tickets(query)
    except Exception as e:
        logger.warning(f"NLP Engine failed or not trained: {str(e)}")
        similar_tickets = []
        
    similar_response = [{"historical_id": t.historical_id, "title": t.title, "similarity_score": s} for t, s in similar_tickets]
    
    if not similar_tickets:
        logger.warning("No similar tickets found above threshold for LLM.")

    # Generate resolutions via LLM
    try:
        resolutions = await llm_engine.generate_resolutions(db_ticket.description, similar_tickets)
    except Exception as e:
        logger.error(f"LLM generation failed: {str(e)}")
        if similar_tickets:
            # Fallback to NLP only
            return {
                "status": "success",
                "ticket_id": ticket_id,
                "resolutions": [], 
                "similar_tickets": similar_response,
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }
        raise HTTPException(status_code=500, detail="AI suggestion generation failed")
    
    # Save resolutions to DB
    db.query(models.Resolution).filter(models.Resolution.ticket_id == ticket_id).delete()
    saved_resolutions = []
    
    for idx, res_text in enumerate(resolutions):
        db_res = models.Resolution(
            ticket_id=ticket_id,
            suggestion_text=res_text,
            order=idx + 1
        )
        db.add(db_res)
        saved_resolutions.append(db_res)
        
    # Update matched ticket counts
    for t, s in similar_tickets:
        db_hist = db.query(models.HistoricalTicket).filter(models.HistoricalTicket.historical_id == t.historical_id).first()
        if db_hist:
            db_hist.times_matched += 1
            
    db.commit()
    for res in saved_resolutions:
        db.refresh(res)
    
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "resolutions": [schemas.ResolutionOut.model_validate(r) for r in saved_resolutions],
        "similar_tickets": similar_response,
        "processing_time_ms": int((time.time() - start_time) * 1000)
    }

# Resolution Feedback Endpoint
@app.post("/resolutions/{resolution_id}/feedback")
@handle_exceptions
async def resolution_feedback(resolution_id: str, feedback: schemas.ResolutionFeedback, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_res = db.query(models.Resolution).filter(models.Resolution.resolution_id == resolution_id).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Resolution not found")
        
    db_res.was_helpful = feedback.was_helpful
    db.commit()
    
    return {"status": "success", "message": "Feedback recorded"}

# Historical Tickets Endpoints
@app.post("/historical-tickets", status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def create_historical_ticket(ticket: schemas.HistoricalTicketCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_hist = models.HistoricalTicket(
        **ticket.model_dump(),
        resolved_at=datetime.utcnow(),
        similarity_score=None,
        times_matched=0
    )
    db.add(db_hist)
    db.commit()
    db.refresh(db_hist)
    
    # Retrain NLP engine
    try:
        all_hist = db.query(models.HistoricalTicket).all()
        nlp_engine.train(all_hist)
    except Exception as e:
        logger.error(f"Failed to retrain NLP engine asynchronously: {str(e)}")
        
    return {"status": "success", "historical_id": db_hist.historical_id}

@app.get("/historical-tickets")
@handle_exceptions
async def get_historical_tickets(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.HistoricalTicket)
    total = query.count()
    tickets = query.all()
    
    return {
        "status": "success",
        "historical_tickets": [schemas.HistoricalTicketFullOut.model_validate(t) for t in tickets],
        "total": total
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute("SELECT 1 FROM sqlite_master LIMIT 1")
    except Exception:
        db_status = "disconnected"
        
    return {
        "status": "healthy",
        "database": db_status,
        "nlp_engine": "ready" if nlp_engine.historical_vectors is not None else "not_trained",
        "llm_engine": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
