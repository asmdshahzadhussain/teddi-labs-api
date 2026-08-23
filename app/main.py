from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging
import os
from app.core.config import settings
from app.db.pool import init_teddi_db, close_teddi_db
from app.routes import generate, admin

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize the database connection pool on startup."""
    try:
        await init_teddi_db(settings.DATABASE_URL)
        logging.info("✅ Database connection established successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to connect to database: {e}")
        raise e


@app.on_event("shutdown")
async def shutdown():
    """Close the database connection pool on shutdown."""
    await close_teddi_db()


app.include_router(generate.router, tags=["TEDDI Entropy"])
app.include_router(admin.router, tags=["TEDDI Admin"])


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the landing page."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "landing", "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>TEDDI Labs</h1><p>Landing page not found.</p>", status_code=404)


@app.get("/health")
async def health():
    """Simple health check to verify database connectivity."""
    from app.db.pool import _pool
    if _pool is None:
        return {"status": "error", "detail": "Database not initialized"}
    return {"status": "operational", "service": "TEDDI Labs Quantum EaaS"}