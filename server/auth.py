"""Authentication utilities for FastAPI routes.

Provides a dependency `get_current_user` that verifies a Supabase-issued
JWT from the `Authorization: Bearer <token>` header and returns a simple
context dict `{ 'user_id': str, 'token': str }`.

Keep this module small and framework-focused; crypto and client setup live
in `config.py`.
"""
from __future__ import annotations

from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import verify_supabase_jwt


_http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> Dict[str, str]:
    """FastAPI dependency that validates a Supabase JWT.

    - Requires Authorization header with scheme 'Bearer'.
    - Returns a dict with 'user_id' and 'token' for downstream use.
    - Raises 401 if missing/invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    ok, user_id, err = verify_supabase_jwt(credentials.credentials)
    if not ok or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err or "Invalid token")

    # Return a backward-compatible shape: include both 'user_id' and 'id'
    # Some existing routers reference user['id'] while new code uses user['user_id'].
    # Keeping both avoids breaking existing endpoints during migration.
    return {"user_id": user_id, "id": user_id, "token": credentials.credentials}


__all__ = ["get_current_user"]
