import logging
from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from app.db.pool import pop_teddi_entropy, validate_api_key
from app.core.mapper import hex_to_teddi_password

router = APIRouter()
logger = logging.getLogger(__name__)

class TEDDIGenerateResponse(BaseModel):
    status: str
    teddi_password: str
    entropy_id: str

async def validate_teddi_key(x_api_key: str = Header(...)):
    """Dependency to validate TEDDI API keys."""
    if not await validate_api_key(x_api_key):
        logger.warning(f"❌ TEDDI Labs: Invalid API Key attempt: {x_api_key[:4]}****")
        raise HTTPException(status_code=403, detail="Invalid TEDDI API Key")
    return x_api_key

@router.post("/generate", response_model=TEDDIGenerateResponse)
async def generate_teddi_password(api_key: str = Depends(validate_teddi_key)):
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