from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_tenant_context
from app.models.sales import Customer, SalesDocument, Service
from app.schemas.sales import (
    CustomerCreate,
    CustomerRead,
    SalesDocumentCreate,
    SalesDocumentRead,
    ServiceCreate,
    ServiceRead,
)

router = APIRouter()


@router.get("/customers", response_model=list[CustomerRead])
async def list_customers(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(Customer).where(Customer.deleted_at.is_(None)))).scalars().all()


@router.post("/customers", response_model=CustomerRead)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    ctx: dict = Depends(get_tenant_context),
):
    row = Customer(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/services", response_model=list[ServiceRead])
async def list_services(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(Service).where(Service.deleted_at.is_(None)))).scalars().all()


@router.post("/services", response_model=ServiceRead)
async def create_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = Service(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/documents", response_model=list[SalesDocumentRead])
async def list_documents(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(SalesDocument).where(SalesDocument.deleted_at.is_(None)))).scalars().all()


@router.post("/documents", response_model=SalesDocumentRead)
async def create_document(payload: SalesDocumentCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = SalesDocument(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
