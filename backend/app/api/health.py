import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.schemas import HealthCheckResponse
from app.integrations.gemini_adapter import gemini_adapter

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    is_gemini_active = gemini_adapter.is_available()

    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
        database_connected=db_connected,
        gemini_connected=is_gemini_active,
        gemini_model=settings.GEMINI_MODEL if is_gemini_active else None,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
