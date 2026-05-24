# ============================================================
# auth_utils.py — JWT Token helpers
# JWT = JSON Web Token → a secure "ID card" for logged-in users
# After login, the server gives a token; the browser sends it
# with every request to prove who they are.
# ============================================================

import jwt                        # PyJWT library
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# -------------------------------------------------------
# CONFIG
# SECRET_KEY: Used to sign/verify tokens (keep this private in production!)
# ALGORITHM: The signing method
# EXPIRE_HOURS: How long before the token expires
# -------------------------------------------------------
SECRET_KEY = "super-secret-key-change-in-production"
ALGORITHM = "HS256"
EXPIRE_HOURS = 24

# This tells FastAPI to look for a Bearer token in the Authorization header
bearer_scheme = HTTPBearer()


def create_token(user_id: int, username: str, role: str) -> str:
    """
    Creates a JWT token containing user info.
    This is like giving a signed ID card to the user after login.
    
    payload = the data we encode inside the token
    exp     = expiry time (token auto-expires after EXPIRE_HOURS)
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """
    Decodes and validates the JWT token.
    Returns the payload (user info) if valid.
    Raises an error if token is expired or tampered.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token. Please login again.")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    FastAPI dependency — extracts and validates the token from the request header.
    Add this as a parameter in any route that requires login.
    
    Example usage in a route:
        @router.get("/me")
        def get_me(user = Depends(get_current_user)):
            return user
    """
    token = credentials.credentials   # Gets the raw token string
    return decode_token(token)


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency — only allows admin users through.
    Add this to any admin-only route.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user