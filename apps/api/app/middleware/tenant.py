from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1") and not request.url.path.startswith("/api/v1/auth"):
            tenant_id = getattr(request.state, "tenant_id", None)
            if not tenant_id and request.url.path != "/health":
                return JSONResponse(status_code=400, content={"detail": "tenant_id missing from JWT"})
        return await call_next(request)
