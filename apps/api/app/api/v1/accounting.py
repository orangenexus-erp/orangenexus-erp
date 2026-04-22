from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_tenant_context
from app.models.accounting import ChartOfAccount, CostCenter, IntegrationRule
from app.schemas.accounting import (
    ChartOfAccountCreate,
    ChartOfAccountRead,
    CostCenterCreate,
    CostCenterRead,
    IntegrationRuleCreate,
    IntegrationRuleRead,
)

router = APIRouter()


@router.get("/chart-of-accounts", response_model=list[ChartOfAccountRead])
async def list_accounts(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(ChartOfAccount).where(ChartOfAccount.deleted_at.is_(None)))).scalars().all()


@router.post("/chart-of-accounts", response_model=ChartOfAccountRead)
async def create_account(
    payload: ChartOfAccountCreate,
    db: AsyncSession = Depends(get_db),
    ctx: dict = Depends(get_tenant_context),
):
    account = ChartOfAccount(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/cost-centers", response_model=list[CostCenterRead])
async def list_cost_centers(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(CostCenter).where(CostCenter.deleted_at.is_(None)))).scalars().all()


@router.post("/cost-centers", response_model=CostCenterRead)
async def create_cost_center(
    payload: CostCenterCreate,
    db: AsyncSession = Depends(get_db),
    ctx: dict = Depends(get_tenant_context),
):
    row = CostCenter(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/integration-rules", response_model=list[IntegrationRuleRead])
async def list_integration_rules(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    return (await db.execute(select(IntegrationRule))).scalars().all()


@router.post("/integration-rules", response_model=IntegrationRuleRead)
async def create_integration_rule(
    payload: IntegrationRuleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: dict = Depends(get_tenant_context),
):
    row = IntegrationRule(tenant_id=ctx["tenant_id"], **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
