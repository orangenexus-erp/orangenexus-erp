from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import safe_decode_token

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

        token = auth_header.removeprefix("Bearer ").strip()
        payload = safe_decode_token(token)
        if not payload:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        if payload.get("type") != "access":
            return JSONResponse(status_code=401, content={"detail": "Invalid token type"})

        required_claims = ("sub", "tenant_id", "role", "branch_id")
        if any(not payload.get(claim) for claim in required_claims):
            return JSONResponse(status_code=401, content={"detail": "Invalid token payload"})

        request.state.user = payload
        request.state.user_id = payload.get("sub")
        request.state.tenant_id = payload.get("tenant_id")
        request.state.role = payload.get("role")
        request.state.branch_id = payload.get("branch_id")

        return await call_next(request)
