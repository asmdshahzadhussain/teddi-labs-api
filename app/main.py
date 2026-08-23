from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging
from app.core.config import settings
from app.db.pool import init_teddi_db, close_teddi_db
from app.routes import generate, admin

logging.basicConfig(level=logging.INFO)

# 1. CREATE THE APP FIRST
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version="1.0.0"
)

# 2. THEN ADD MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. THEN ADD LIFESPAN EVENTS
@app.on_event("startup")
async def startup():
    await init_teddi_db(settings.DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await close_teddi_db()

# 4. THEN ADD YOUR ROUTES
app.include_router(generate.router, tags=["TEDDI Entropy"])
app.include_router(admin.router, tags=["TEDDI Admin"])

# 5. THEN ADD YOUR CUSTOM ROUTES (LIKE /docs)
@app.get("/docs", response_class=HTMLResponse)
async def api_docs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TEDDI Labs — API Reference</title>
        <style>
            body{background:#06060e;color:#f4f4f9;font-family:sans-serif;padding:40px 20px}
            .container{max-width:900px;margin:0 auto}
            h1{font-size:42px;background:linear-gradient(135deg,#00d4ff,#7b2ffc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
            .endpoint{background:#0c0c18;border:1px solid #1a1a2e;border-radius:12px;padding:20px;margin:16px 0}
            .method{color:#00d4ff;font-weight:bold}
            .path{color:#f4f4f9;font-family:monospace}
            .code{background:#06060e;padding:12px;border-radius:6px;font-family:monospace;color:#50fa7b;font-size:14px;overflow-x:auto;white-space:pre-wrap}
            .note{color:#6b6b82;font-size:14px;border-left:3px solid #7b2ffc;padding-left:16px;margin:12px 0}
            .links{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}
            .links a{color:#00d4ff;text-decoration:none;padding:8px 20px;border:1px solid rgba(0,212,255,0.2);border-radius:8px}
            .links a:hover{background:rgba(0,212,255,0.08)}
            .footer{margin-top:40px;color:#444;font-size:12px}
            .footer a{color:#6b6b82;text-decoration:none}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>⚡ TEDDI Labs</h1>
        <p style="color:#a6a6bd;font-size:18px;">API Reference — Quantum Entropy for the Enterprise</p>

        <div class="links">
            <a href="/">🏠 Home</a>
            <a href="https://teddi-landing.onrender.com">🌐 Landing Page</a>
            <a href="https://teddi-landing.onrender.com#pricing">💰 Pricing</a>
        </div>

        <h2 style="color:#f4f4f9;margin-top:32px;">Endpoints</h2>

        <div class="endpoint">
            <div><span class="method">POST</span> <span class="path">/generate</span></div>
            <p style="color:#a6a6bd;font-size:14px;">Generate a quantum password with a traceable entropy_id.</p>
            <div style="font-size:13px;color:#6b6b82;margin:8px 0;">Headers:</div>
            <div class="code">X-API-Key: your_api_key</div>
            <div style="font-size:13px;color:#6b6b82;margin:8px 0;">Example Response:</div>
            <div class="code">{
        "status": "success",
        "teddi_password": "K#pL9!mQ@xZ2$vR7...",
        "entropy_id": "a3f8c2d1-9e4f-4b6c-8d7e-1a2b3c4d5e6f"
        }</div>
    </div>

    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/refill</span></div>
        <p style="color:#a6a6bd;font-size:14px;">Admin: Refill the quantum pool with fresh entropy.</p>
        <div style="font-size:13px;color:#6b6b82;margin:8px 0;">Headers:</div>
        <div class="code">X-TEDDI-Admin-Key: your_admin_key</div>
    </div>

    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/admin/create-key</span></div>
        <p style="color:#a6a6bd;font-size:14px;">Admin: Generate a new customer API key.</p>
        <div style="font-size:13px;color:#6b6b82;margin:8px 0;">Headers:</div>
        <div class="code">X-TEDDI-Admin-Key: your_admin_key</div>
        <div style="font-size:13px;color:#6b6b82;margin:8px 0;">Query Parameter:</div>
        <div class="code">?client_name=CustomerName</div>
    </div>

    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/health</span></div>
        <p style="color:#a6a6bd;font-size:14px;">Check if the API is operational.</p>
        <div style="font-size:13px;color:#6b6b82;margin:8px 0;">Example Response:</div>
        <div class="code">{"status":"operational","service":"TEDDI Labs Quantum EaaS"}</div>
    </div>

    <div class="note">
        <strong style="color:#f4f4f9;">Get a Free API Key</strong><br>
        Visit our landing page to request access: <a href="https://teddi-landing.onrender.com" style="color:#00d4ff;">teddi-landing.onrender.com</a>
    </div>

    <div class="footer">
        <a href="mailto:admin@yourcompany.com">Contact</a> · TEDDI Labs — Quantum Entropy for the Enterprise
    </div>
</div>
</body>
</html>
"""

# 6. THEN ADD THE ROOT ROUTE
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TEDDI Labs</title>
        <style>
            body {
                background: #06060e;
                color: #f4f4f9;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                padding: 20px;
                text-align: center;
            }
            .container {
                max-width: 600px;
            }
            h1 {
                font-size: 48px;
                font-weight: 800;
                background: linear-gradient(135deg, #00d4ff, #7b2ffc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 8px;
            }
            .subtitle {
                color: #a6a6bd;
                font-size: 18px;
                margin-bottom: 32px;
            }
            .links {
                display: flex;
                gap: 16px;
                justify-content: center;
                flex-wrap: wrap;
            }
            .links a {
                color: #00d4ff;
                text-decoration: none;
                padding: 10px 24px;
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 8px;
                transition: 0.2s;
                font-size: 14px;
            }
            .links a:hover {
                background: rgba(0, 212, 255, 0.08);
                border-color: #00d4ff;
            }
            .status {
                margin-top: 40px;
                font-size: 14px;
                color: #6b6b82;
            }
            .status .dot {
                display: inline-block;
                width: 10px;
                height: 10px;
                background: #3fe08a;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 12px rgba(63, 224, 138, 0.4);
            }
            .status .live {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .footer {
                margin-top: 48px;
                font-size: 12px;
                color: #444;
            }
            .footer a {
                color: #6b6b82;
                text-decoration: none;
            }
            .footer a:hover {
                color: #a6a6bd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TEDDI Labs</h1>
            <p class="subtitle">Quantum Entropy for the Enterprise</p>
            <div class="links">
                <a href="https://teddi-landing.onrender.com" target="_blank">→ Landing Page</a>
                <a href="/docs" target="_blank">→ API Documentation</a>
                <a href="https://teddi-landing.onrender.com#pricing" target="_blank">→ Pricing</a>
            </div>
            <div class="status">
                <div class="live">
                    <span class="dot"></span> API Status: Operational
                </div>
            </div>
            <div class="footer">
                <a href="mailto:admin@yourcompany.com">Contact</a>
            </div>
        </div>
    </body>
    </html>
    """