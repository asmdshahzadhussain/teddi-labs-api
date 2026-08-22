import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from app.db.pool import pop_teddi_entropy, _pool
from app.core.mapper import hex_to_teddi_password

router = APIRouter()
logger = logging.getLogger(__name__)

class TEDDIGenerateResponse(BaseModel):
    status: str
    teddi_password: str
    entropy_id: str

async def validate_and_track_key(x_api_key: str = Header(...)):
    """Validate key, check expiry, enforce limits, and track usage."""
    if not _pool:
        raise HTTPException(status_code=503, detail="TEDDI Service Unavailable")
    
    async with _pool.acquire() as conn:
        # Fetch key details
        row = await conn.fetchrow(
            """
            SELECT key_string, client_name, is_active, expires_at, 
                   monthly_limit, usage_count, last_reset_at
            FROM api_keys 
            WHERE key_string = $1
            """,
            x_api_key
        )
        
        if not row:
            logger.warning(f"❌ Invalid API Key attempt: {x_api_key[:4]}****")
            raise HTTPException(status_code=403, detail="Invalid TEDDI API Key")
        
        # 1. Check if active
        if not row['is_active']:
            raise HTTPException(status_code=403, detail="TEDDI API Key is deactivated")
        
        # 2. Check expiry
        if row['expires_at'] and row['expires_at'] < datetime.now():
            raise HTTPException(status_code=403, detail="TEDDI API Key has expired. Please renew your subscription.")
        
        # 3. Reset usage count if a month has passed (billing cycle)
        if row['last_reset_at'] and row['last_reset_at'] < datetime.now() - timedelta(days=30):
            await conn.execute(
                "UPDATE api_keys SET usage_count = 0, last_reset_at = NOW() WHERE key_string = $1",
                x_api_key
            )
            current_usage = 0
        else:
            current_usage = row['usage_count']
        
        # 4. Check monthly limit
        if current_usage >= row['monthly_limit']:
            raise HTTPException(
                status_code=429, 
                detail=f"Monthly request limit of {row['monthly_limit']} reached. Please upgrade your tier."
            )
        
        # 5. Increment usage count
        await conn.execute(
            "UPDATE api_keys SET usage_count = usage_count + 1 WHERE key_string = $1",
            x_api_key
        )
        
        return x_api_key

@router.post("/generate", response_model=TEDDIGenerateResponse)
async def generate_teddi_password(api_key: str = Depends(validate_and_track_key)):
    """
    TEDDI Endpoint: Instantly returns a quantum-sourced, high-entropy password.
    Utilizes pre-fetched quantum randomness for sub-50ms response times.
    """
    try:
        entropy_id, raw_hex = await pop_teddi_entropy()
        password = hex_to_teddi_password(raw_hex)
        logger.info(f"✅ TEDDI served entropy {entropy_id}")
        return TEDDIGenerateResponse(
            status="success",
            teddi_password=password,
            entropy_id=str(entropy_id)
        )
    except Exception as e:
        logger.error(f"TEDDI Generate failed: {e}")
        raise HTTPException(status_code=503, detail=f"TEDDI Error: {str(e)}")