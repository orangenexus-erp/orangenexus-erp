from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.core import Tenant
from app.schemas.core import TenantCreate, TenantRead

router = APIRouter()


@router.get("/", response_model=list[TenantRead])
async def list_tenants(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    rows = (await db.execute(select(Tenant).where(Tenant.deleted_at.is_(None)))).scalars().all()
    return rows


@router.post("/", response_model=TenantRead)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    tenant = Tenant(name=payload.name, tax_id=payload.tax_id)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant
