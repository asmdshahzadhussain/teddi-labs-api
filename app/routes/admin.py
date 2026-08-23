import logging
import httpx
import secrets
import string
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from app.db.pool import bulk_insert_teddi_entropy, _pool
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ==========================================
# RESPONSE MODELS
# ==========================================
class TEDDIRefillResponse(BaseModel):
    status: str
    inserted_count: int
    message: str

class TEDDIKeyResponse(BaseModel):
    status: str
    api_key: str
    client_name: str
    message: str


# ==========================================
# POST /refill (For YOUR cron job)
# ==========================================
@router.post("/refill", response_model=TEDDIRefillResponse)
async def refill_teddi_pool(x_admin_key: str = Header(..., alias="X-TEDDI-Admin-Key")):
    if x_admin_key != settings.ADMIN_API_KEY:
        logger.warning("🚫 Unauthorized /refill attempt")
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


# ==========================================
# GET /health (For cron-job.org)
# ==========================================
@router.get("/health")
async def teddi_health():
    return {"status": "operational", "service": "TEDDI Labs Quantum EaaS"}


# ==========================================
# POST /admin/create-key (For onboarding clients)
# ==========================================
@router.post("/admin/create-key", response_model=TEDDIKeyResponse)
async def create_customer_key(
    client_name: str,
    x_admin_key: str = Header(..., alias="X-TEDDI-Admin-Key")
):
    if x_admin_key != settings.ADMIN_API_KEY:
        logger.warning("🚫 Unauthorized key creation attempt")
        raise HTTPException(status_code=403, detail="Invalid TEDDI Admin Key")

    alphabet = string.ascii_uppercase + string.digits
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(8))
    new_key = f"TEDDI_PROD_{random_suffix}"

    if not _pool:
        raise HTTPException(status_code=503, detail="Database not initialized")

    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO api_keys (key_string, client_name, is_active) VALUES ($1, $2, true)",
            new_key, client_name
        )

    return TEDDIKeyResponse(
        status="success",
        api_key=new_key,
        client_name=client_name,
        message=f"API key created for {client_name}. Give this to your customer!"
    )