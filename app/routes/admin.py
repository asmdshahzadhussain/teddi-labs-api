import logging
import httpx
import secrets
import string
from fastapi import APIRouter, HTTPException, Header, status
from fastapi.responses import HTMLResponse  # <-- ADD THIS IMPORT
from pydantic import BaseModel
from app.db.pool import bulk_insert_teddi_entropy
from app.core.config import settings

# ==========================================
# 1. CREATE THE ROUTER FIRST
# ==========================================
router = APIRouter()
logger = logging.getLogger(__name__)

# ==========================================
# 2. THEN ADD YOUR ROUTES
# ==========================================

# --- HUMAN-FRIENDLY PAGES FOR ADMIN ENDPOINTS ---
@router.get("/refill", response_class=HTMLResponse)
async def refill_info():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>TEDDI Labs</title>
    <style>
        body{background:#06060e;color:#f4f4f9;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;padding:20px;text-align:center}
        .container{max-width:600px}
        h1{font-size:36px;background:linear-gradient(135deg,#00d4ff,#7b2ffc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .code{background:#0c0c18;padding:12px;border-radius:8px;font-family:monospace;color:#00d4ff;text-align:left;margin:20px 0}
        .links a{color:#00d4ff;text-decoration:none;padding:8px 16px;border:1px solid rgba(0,212,255,0.2);border-radius:6px;margin:4px;display:inline-block}
        .links a:hover{background:rgba(0,212,255,0.08)}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>⚡ TEDDI Labs</h1>
        <p style="color:#a6a6bd;">This endpoint is for admin use only.</p>
        <p style="color:#6b6b82;font-size:14px;">To refill the quantum pool, use:</p>
        <div class="code">POST /refill<br>X-TEDDI-Admin-Key: your_admin_key</div>
        <div class="links">
            <a href="/docs">📚 API Docs</a>
            <a href="https://teddi-landing.onrender.com">🌐 Landing Page</a>
        </div>
        <p style="color:#444;font-size:12px;margin-top:32px;">TEDDI Labs — Quantum Entropy for the Enterprise</p>
    </div>
    </body>
    </html>
    """

@router.get("/admin/create-key", response_class=HTMLResponse)
async def create_key_info():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>TEDDI Labs</title>
    <style>
        body{background:#06060e;color:#f4f4f9;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;padding:20px;text-align:center}
        .container{max-width:600px}
        h1{font-size:36px;background:linear-gradient(135deg,#00d4ff,#7b2ffc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .code{background:#0c0c18;padding:12px;border-radius:8px;font-family:monospace;color:#00d4ff;text-align:left;margin:20px 0}
        .links a{color:#00d4ff;text-decoration:none;padding:8px 16px;border:1px solid rgba(0,212,255,0.2);border-radius:6px;margin:4px;display:inline-block}
        .links a:hover{background:rgba(0,212,255,0.08)}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>🔑 TEDDI Labs</h1>
        <p style="color:#a6a6bd;">This endpoint is for admin use only.</p>
        <p style="color:#6b6b82;font-size:14px;">To create a customer API key, use:</p>
        <div class="code">POST /admin/create-key?client_name=Customer<br>X-TEDDI-Admin-Key: your_admin_key</div>
        <div class="links">
            <a href="/docs">📚 API Docs</a>
            <a href="https://teddi-landing.onrender.com">🌐 Landing Page</a>
        </div>
        <p style="color:#444;font-size:12px;margin-top:32px;">TEDDI Labs — Quantum Entropy for the Enterprise</p>
    </div>
    </body>
    </html>
    """

# ==========================================
# 3. THEN ADD YOUR EXISTING POST ROUTES
# ==========================================

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

# ==========================================
# 4. HEALTH CHECK
# ==========================================
@router.get("/health")
async def teddi_health():
    return {"status": "operational", "service": "TEDDI Labs Quantum EaaS"}

# ==========================================
# 5. CREATE CUSTOMER KEY ENDPOINT
# ==========================================
class TEDDIKeyResponse(BaseModel):
    status: str
    api_key: str
    client_name: str
    message: str

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
    
    from app.db.pool import _pool
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