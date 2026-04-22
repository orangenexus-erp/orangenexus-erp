from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_tenant_context
from app.models.treasury import BankAccount, TreasuryMovement
from app.schemas.treasury import BankAccountCreate, BankAccountRead, TreasuryMovementCreate, TreasuryMovementRead

router = APIRouter()


@router.get("/bank-accounts", response_model=list[BankAccountRead])
async def list_bank_accounts(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(BankAccount).where(BankAccount.deleted_at.is_(None)))).scalars().all()


@router.post("/bank-accounts", response_model=BankAccountRead)
async def create_bank_account(payload: BankAccountCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = BankAccount(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/movements", response_model=list[TreasuryMovementRead])
async def list_movements(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(TreasuryMovement).where(TreasuryMovement.deleted_at.is_(None)))).scalars().all()


@router.post("/movements", response_model=TreasuryMovementRead)
async def create_movement(payload: TreasuryMovementCreate, db: AsyncSession = Depends(get_db), ctx: dict = Depends(get_tenant_context)):
    row = TreasuryMovement(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
