import logging
import httpx
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from app.db.pool import bulk_insert_teddi_entropy
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class TEDDIRefillResponse(BaseModel):
    status: str
    inserted_count: int
    message: str

@router.post("/refill", response_model=TEDDIRefillResponse)
async def refill_teddi_pool(x_admin_key: str = Header(..., alias="X-TEDDI-Admin-Key")):
    """
    TEDDI Admin: Fetches 100 fresh quantum hex blocks from ANU QRNG 
    and refills the internal buffer pool.
    """
    if x_admin_key != settings.ADMIN_API_KEY:
        logger.warning("🚫 TEDDI Labs: Unauthorized /refill attempt")
        raise HTTPException(status_code=403, detail="Invalid TEDDI Admin Key")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                settings.ANU_API_URL,
                params={"length": settings.ANU_BATCH_SIZE, "type": "hex16", "size": 16}
            )
            response.raise_for_status()
            payload = response.json()
            
            if "data" not in payload:
                raise HTTPException(status_code=502, detail="TEDDI Source (ANU) malformed")
            
            hex_blocks = payload["data"]
            inserted = await bulk_insert_teddi_entropy(hex_blocks)
            logger.info(f"🌌 TEDDI Labs: Refilled {inserted} quantum blocks.")
            return TEDDIRefillResponse(
                status="success",
                inserted_count=inserted,
                message=f"TEDDI buffer recharged with {inserted} fresh entropy seeds."
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="TEDDI Quantum Source Timeout")
    except Exception as e:
        logger.exception(f"TEDDI Refill critical error: {e}")
        raise HTTPException(status_code=500, detail="TEDDI Refill failed")

@router.get("/health")
async def teddi_health():
    return {"status": "operational", "service": "TEDDI Labs Quantum EaaS"}