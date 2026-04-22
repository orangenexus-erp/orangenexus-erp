from fastapi import APIRouter

from app.api.v1 import accounting, auth, purchases, sales, tenants, treasury, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounting.router, prefix="/accounting", tags=["accounting"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(treasury.router, prefix="/treasury", tags=["treasury"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
