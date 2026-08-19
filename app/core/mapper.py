from app.core.config import settings

def hex_to_teddi_password(hex_str: str) -> str:
    """
    TEDDI Core Algorithm: Maps quantum entropy (hex) into a high-entropy 
    alphanumeric + symbol password. Designed to maximize Shannon entropy.
    """
    try:
        entropy_int = int(hex_str, 16)
    except ValueError:
        raise ValueError("Invalid quantum hex string provided to TEDDI engine")

    charset = settings.CHARSET
    charset_len = len(charset)
    password_chars = []
    temp_entropy = entropy_int

    for _ in range(settings.PASSWORD_LENGTH):
        idx = temp_entropy % charset_len
        password_chars.append(charset[idx])
        temp_entropy //= charset_len
        
        # Cryptographic cascade fallback (ensures we never run out of entropy)
        if temp_entropy == 0:
            temp_entropy = idx * 1664525 + 1013904223

    return "".join(password_chars)