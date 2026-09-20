"""
Sari-Sari Store POS — Authentication & Session Verification Dependency
========================================================================
Validates admin session tokens on sensitive endpoints to prevent Broken
Object Level Authorization (BOLA) and unauthenticated data manipulation.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Header, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db

security = HTTPBearer(auto_error=False)


async def verify_admin_token(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    token_query: Optional[str] = Query(None, alias="token"),
    db=Depends(get_db),
) -> str:
    """
    FastAPI dependency that enforces a valid, non-expired admin session.
    Checks (in priority):
      1. HTTP Bearer header: `Authorization: Bearer <token>`
      2. Header: `X-Admin-Token: <token>`
      3. Query parameter: `?token=<token>` (useful for file download links)
    """
    token = None
    if auth and auth.credentials:
        token = auth.credentials.strip()
    elif x_admin_token:
        token = x_admin_token.strip()
    elif token_query:
        token = token_query.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Admin session token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check database for active session
    cursor = await db.execute(
        "SELECT token, expires_at FROM admin_sessions WHERE token = ? AND expires_at > datetime('now')",
        (token,)
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Admin session token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
