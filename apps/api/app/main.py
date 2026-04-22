from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.tenant import TenantValidationMiddleware

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(TenantValidationMiddleware)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "api", "version": settings.app_version}


app.include_router(api_router)
