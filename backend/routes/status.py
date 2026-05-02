import os
import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from services.key_manager import key_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Optional admin token for protected status endpoint
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_STATUS_TOKEN = os.getenv("ADMIN_STATUS_TOKEN")


def _require_admin_token(x_admin_token: str = Header(None)):
    """
    Dependency that requires X-Admin-Token header to match ADMIN_STATUS_TOKEN.
    If the env var is not set, the endpoint is locked down (403 always).
    """
    if not ADMIN_STATUS_TOKEN:
        logger.error("ADMIN_STATUS_TOKEN not configured — admin endpoints locked")
        raise HTTPException(status_code=403, detail="Admin endpoint not configured")
    if not x_admin_token or x_admin_token != ADMIN_STATUS_TOKEN:
        logger.warning("Unauthorized attempt to access admin status endpoint")
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


# ---------------------------------------------------------------------------
# PUBLIC: minimal health info (safe to expose)
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Public health check for load balancers / monitoring tools.
    Returns minimal info — no secrets, no operational details.
    """
    checks = {}
    overall_healthy = True

    # DB check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        checks["database"] = "error"
        overall_healthy = False

    # Gemini keys check (boolean only — no counts/details)
    try:
        keys_status = key_manager.get_status()
        available = sum(1 for k in keys_status if k["available"])
        if len(keys_status) == 0:
            checks["gemini"] = "not_configured"
            overall_healthy = False
        elif available == 0:
            checks["gemini"] = "exhausted"
            overall_healthy = False
            logger.warning("⚠️ Service degraded: all Gemini keys exhausted")
        else:
            checks["gemini"] = "ok"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        checks["gemini"] = "error"
        overall_healthy = False

    response_body = {
        "status": "healthy" if overall_healthy else "degraded",
        "checks": checks,
    }

    # Return 503 when degraded so monitoring tools alert
    if not overall_healthy:
        return JSONResponse(status_code=503, content=response_body)
    return response_body


# ---------------------------------------------------------------------------
# ADMIN: detailed status (requires X-Admin-Token header)
# ---------------------------------------------------------------------------
@router.get("/status")
async def get_api_status(_: bool = Depends(_require_admin_token)):
    """
    Returns detailed health status of all Gemini API keys.
    Requires X-Admin-Token header.
    """
    keys_status = key_manager.get_status()
    available_count = sum(1 for k in keys_status if k["available"])

    response_body = {
        "total_keys": len(keys_status),
        "available_keys": available_count,
        "all_exhausted": available_count == 0 and len(keys_status) > 0,
        "keys": keys_status,
    }

    # Return 503 if no keys available so monitoring tools alert
    if len(keys_status) > 0 and available_count == 0:
        logger.warning("⚠️ All Gemini keys exhausted — service degraded")
        return JSONResponse(status_code=503, content=response_body)

    return response_body