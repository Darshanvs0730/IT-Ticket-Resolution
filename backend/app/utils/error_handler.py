import logging
import time
from logging.handlers import TimedRotatingFileHandler
import os
from functools import wraps
from fastapi import HTTPException

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("itticket")
logger.setLevel(logging.INFO)

# Daily rotating log
log_filename = os.path.join(log_dir, "itticket.log")
handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=30)
handler.suffix = "%Y%m%d.log"
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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

def handle_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            raise HTTPException(status_code=401, detail=str(e))
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            raise HTTPException(status_code=422, detail=str(e))
        except (DatabaseError, ITTicketError) as e:
            logger.error(f"System error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="An internal server error occurred")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
    return wrapper

def retry_on_error(max_retries=3, backoff=2.0, exception_types=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}. Error: {str(e)}")
                        raise
                    sleep_time = backoff ** retries
                    logger.warning(f"Error in {func.__name__}: {str(e)}. Retrying in {sleep_time}s ({retries}/{max_retries})...")
                    time.sleep(sleep_time)
            return func(*args, **kwargs)
        return wrapper
    return decorator
