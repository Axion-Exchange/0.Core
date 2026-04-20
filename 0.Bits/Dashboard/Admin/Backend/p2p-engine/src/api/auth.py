"""
API Key Authentication Middleware
=================================
Validates X-API-Key header against API_SECRET_KEY environment variable.
All routes except health check require authentication.
"""

import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# Header-based API key
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key() -> str:
    """Get the configured API secret key from environment.
    
    M3: Refuses to start without API_SECRET_KEY — never auto-generates.
    """
    key = os.getenv("API_SECRET_KEY", "")
    if not key:
        raise RuntimeError(
            "🚨 FATAL: API_SECRET_KEY environment variable is not set.\n"
            "   Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
            "   Then add API_SECRET_KEY=<your-key> to your .env file."
        )
    return key


async def verify_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """FastAPI dependency that validates the API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )
    
    expected = get_api_key()
    if not secrets.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    
    return api_key
