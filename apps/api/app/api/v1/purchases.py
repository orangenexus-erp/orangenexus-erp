from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_tenant_context
from app.models.purchases import PurchaseDocument, Supplier, TaxWithholding
from app.schemas.purchases import (
    PurchaseDocumentCreate,
    PurchaseDocumentRead,
    SupplierCreate,
    SupplierRead,
    TaxWithholdingCreate,
    TaxWithholdingRead,
)

router = APIRouter()


@router.get("/suppliers", response_model=list[SupplierRead])
async def list_suppliers(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(Supplier).where(Supplier.deleted_at.is_(None)))).scalars().all()


@router.post("/suppliers", response_model=SupplierRead)
async def create_supplier(payload: SupplierCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = Supplier(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/documents", response_model=list[PurchaseDocumentRead])
async def list_documents(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(PurchaseDocument).where(PurchaseDocument.deleted_at.is_(None)))).scalars().all()


@router.post("/documents", response_model=PurchaseDocumentRead)
async def create_document(payload: PurchaseDocumentCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = PurchaseDocument(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/withholdings", response_model=list[TaxWithholdingRead])
async def list_withholdings(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(TaxWithholding).where(TaxWithholding.deleted_at.is_(None)))).scalars().all()


@router.post("/withholdings", response_model=TaxWithholdingRead)
async def create_withholding(payload: TaxWithholdingCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = TaxWithholding(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
