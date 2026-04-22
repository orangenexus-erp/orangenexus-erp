from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session


async def get_db(request: Request, db: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    tenant_id = getattr(request.state, "tenant_id", None)
    user_id = getattr(request.state, "user_id", None)

    if tenant_id:
        await db.execute(text("SET app.current_tenant = :tenant_id"), {"tenant_id": str(tenant_id)})
    if user_id:
        await db.execute(text("SET app.current_user = :user_id"), {"user_id": str(user_id)})

    yield db


async def get_current_user(request: Request) -> dict:
    user_payload = getattr(request.state, "user", None)
    if not user_payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user_payload


async def get_tenant_context(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context missing")
    return str(tenant_id)
