from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChartOfAccountCreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    nature: str
    level: int


class ChartOfAccountRead(ChartOfAccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class CostCenterCreate(BaseModel):
    code: str
    name: str


class CostCenterRead(CostCenterCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class JournalEntryLineCreate(BaseModel):
    account_id: UUID
    movement_type: str
    original_currency: str
    original_amount: Decimal
    amount_ves: Decimal
    amount_usd: Decimal


class JournalEntryCreate(BaseModel):
    branch_id: UUID
    accounting_date: date
    entry_type: str
    description: str
    lines: list[JournalEntryLineCreate]


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    entry_number: str
    accounting_date: date
    status: str


class IntegrationRuleCreate(BaseModel):
    event: str
    debit_account_id: UUID
    credit_account_id: UUID
    amount_formula: str
    priority: int = 1


class IntegrationRuleRead(IntegrationRuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
