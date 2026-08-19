import logging
import httpx
import secrets
import string
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from app.db.pool import bulk_insert_teddi_entropy
from app.core.config import settings

# ==========================================
# ROUTER & LOGGER
# ==========================================
router = APIRouter()
logger = logging.getLogger(__name__)

# ==========================================
# PYDANTIC RESPONSE MODELS
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
# ENDPOINT: /refill (Admin - Refill Quantum Pool)
# ==========================================
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
            # CRITICAL: ANU requires 'size' parameter for hex16 type!
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
# ENDPOINT: /health (Health Check for Cron Jobs)
# ==========================================
@router.get("/health")
async def teddi_health():
    return {"status": "operational", "service": "TEDDI Labs Quantum EaaS"}

# ==========================================
# ENDPOINT: /admin/create-key (Create Customer API Key)
# ==========================================
@router.post("/admin/create-key", response_model=TEDDIKeyResponse)
async def create_customer_key(
    client_name: str,
    x_admin_key: str = Header(..., alias="X-TEDDI-Admin-Key")
):
    """
    TEDDI Admin: Generate a new API key for a customer instantly.
    No need to touch Supabase manually. Perfect for live demos.
    """
    # 1. Verify the admin key
    if x_admin_key != settings.ADMIN_API_KEY:
        logger.warning("🚫 Unauthorized key creation attempt")
        raise HTTPException(status_code=403, detail="Invalid TEDDI Admin Key")

    # 2. Generate a secure, human-readable customer key
    # Format: TEDDI_PROD_XXXXXXXX (8 random alphanumeric chars)
    alphabet = string.ascii_uppercase + string.digits
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(8))
    new_key = f"TEDDI_PROD_{random_suffix}"
    
    # 3. Insert into Supabase
    try:
        from app.db.pool import _pool
        if not _pool:
            raise HTTPException(status_code=503, detail="Database not initialized")
            
        async with _pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO api_keys (key_string, client_name, is_active) VALUES ($1, $2, true)",
                new_key, client_name
            )
        
        logger.info(f"🔑 Created new customer key {new_key} for {client_name}")
        return TEDDIKeyResponse(
            status="success",
            api_key=new_key,
            client_name=client_name,
            message=f"API key created for {client_name}. Give this to your customer!"
        )
    except Exception as e:
        logger.error(f"Failed to create key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer key")