from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.db.pool import init_teddi_db, close_teddi_db
from app.routes import generate, admin

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version="1.0.0"
)

# CORS - Open for enterprise integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_teddi_db(settings.DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await close_teddi_db()

app.include_router(generate.router, tags=["TEDDI Entropy"])
app.include_router(admin.router, tags=["TEDDI Admin"])

@app.get("/")
async def root():
    return {
        "service": "TEDDI Labs",
        "status": "Quantum Operational",
        "docs": "/docs",
        "version": "1.0.0"
    }