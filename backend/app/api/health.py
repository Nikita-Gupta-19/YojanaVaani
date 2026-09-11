from fastapi import APIRouter
from app.core.database import check_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """Health check endpoint verifying application and database readiness."""
    db_ok = check_db_connection()
    return {
        "status": "ok",
        "database": "connected" if db_ok else "disconnected",
    }
