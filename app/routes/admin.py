# Add these at the top of admin.py, after the imports
from fastapi.responses import HTMLResponse

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