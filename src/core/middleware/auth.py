from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

class DashboardAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip auth for docs and openapi.json
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Skip auth for non-dashboard routes
        if not request.url.path.startswith("/api/v1/dashboard"):
            return await call_next(request)

        # Get authorization header
        auth_header: Optional[str] = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format. Use 'Bearer your-token'",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        # Verify dashboard token
        if token != settings.DASHBOARD_SECRET_KEY:
            raise HTTPException(
                status_code=401,
                detail="Invalid dashboard token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Token is valid, continue with the request
        return await call_next(request)

# Dependency for protecting specific routes
async def verify_dashboard_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != settings.DASHBOARD_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid dashboard token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True 