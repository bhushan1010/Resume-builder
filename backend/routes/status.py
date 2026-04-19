from fastapi import APIRouter
from services.key_manager import key_manager

router = APIRouter()

@router.get("/status")
async def get_api_status():
    """
    Returns health status of all Gemini API keys.
    No auth required (useful for debugging).
    """
    keys_status = key_manager.get_status()
    available_count = sum(1 for k in keys_status if k["available"])
    
    return {
        "total_keys": len(keys_status),
        "available_keys": available_count,
        "all_exhausted": available_count == 0,
        "keys": keys_status
    }