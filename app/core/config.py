import os
from dotenv import load_dotenv

load_dotenv()

class TEDDISettings:
    # === DATABASE ===
    DATABASE_URL: str = os.getenv("TEDDI_DATABASE_URL", "")
    
    # === SECURITY ===
    ADMIN_API_KEY: str = os.getenv("TEDDI_ADMIN_API_KEY", "TEDDI_ADMIN_REFILL_2026")
    
    # === QUANTUM SOURCE (ANU) ===
    ANU_API_URL: str = "https://qrng.anu.edu.au/API/jsonI.php"
    ANU_BATCH_SIZE: int = 100
    
    # === PASSWORD GENERATION ===
    PASSWORD_LENGTH: int = 32
    CHARSET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"

    # === BRANDING ===
    API_TITLE: str = "TEDDI Labs - Quantum Entropy API"
    API_DESCRIPTION: str = "Trusted Entropy Distribution & Digital Infrastructure. Generate unhackable, quantum-sourced passwords for Web3, AI, and enterprise security."

settings = TEDDISettings()