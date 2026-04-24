from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, get_db, get_tenant_context
from app.models.sales import Customer, SalesDocument, Service
from app.schemas.core import APIMessage
from app.schemas.sales import (
    CustomerCreate,
    CustomerRead,
    SalesDocumentCreate,
    SalesDocumentRead,
    SalesDocumentResponse,
    SalesDocumentUpdate,
    ServiceCreate,
    ServiceRead,
)

router = APIRouter()

DRAFT_STATUS = "DRAFT"
POSTED_STATUS = "POSTED"


async def _get_tenant_sales_document_or_404(
    db: AsyncSession,
    document_id: UUID,
    tenant_id: UUID,
) -> SalesDocument:
    result = await db.execute(
        select(SalesDocument)
        .options(selectinload(SalesDocument.items))
        .where(
            SalesDocument.id == document_id,
            SalesDocument.tenant_id == tenant_id,
            SalesDocument.deleted_at.is_(None),
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales document not found")
    return document


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


@router.put("/documents/{document_id}", response_model=SalesDocumentResponse)
async def update_sales_document(
    document_id: UUID,
    payload: SalesDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_context: dict = Depends(get_tenant_context),
):
    """Update a sales document only while it remains in DRAFT state."""
    db_document = await _get_tenant_sales_document_or_404(db, document_id, tenant_context["tenant_id"])

    current_status = (db_document.status or "").upper()

    if current_status == POSTED_STATUS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update posted documents (accounting immutability)",
        )

    if current_status != DRAFT_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update document in status '{db_document.status}'. Only DRAFT documents are editable.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(db_document, field_name, field_value)

    await db.commit()
    await db.refresh(db_document)
    return db_document


@router.delete("/documents/{document_id}", response_model=APIMessage)
async def delete_sales_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_context: dict = Depends(get_tenant_context),
):
    """Soft-delete a sales document only while it remains in DRAFT state."""
    db_document = await _get_tenant_sales_document_or_404(db, document_id, tenant_context["tenant_id"])

    current_status = (db_document.status or "").upper()

    if current_status == POSTED_STATUS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete posted documents (accounting immutability)",
        )

    if current_status != DRAFT_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete document in status '{db_document.status}'. Only DRAFT documents are deletable.",
        )

    await db.delete(db_document)
    await db.commit()
    return APIMessage(detail="Sales document deleted successfully")


@router.post("/documents/{document_id}/post", response_model=SalesDocumentResponse)
async def post_sales_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_context: dict = Depends(get_tenant_context),
):
    """
    Post (publish) a sales document.

    Business rules:
    - Only documents with status='DRAFT' can be posted
    - Once posted, status changes to 'POSTED'
    - Posted documents cannot be edited or deleted (accounting immutability)
    - Only the document owner (tenant) can post it

    Returns:
        The updated sales document with status='POSTED'

    Raises:
        404: Document not found
        400: Document is not in DRAFT status
    """
    db_document = await _get_tenant_sales_document_or_404(db, document_id, tenant_context["tenant_id"])

    current_status = (db_document.status or "").upper()

    if current_status != DRAFT_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot post document in status '{db_document.status}'. Only DRAFT documents can be posted.",
        )

    db_document.status = POSTED_STATUS

    await db.commit()
    await db.refresh(db_document)
    return db_document
