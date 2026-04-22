from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BankAccountCreate(BaseModel):
    branch_id: UUID | None = None
    bank_name: str
    account_number: str
    currency: str
    ledger_account_id: UUID


class BankAccountRead(BankAccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class TreasuryMovementCreate(BaseModel):
    branch_id: UUID
    bank_account_id: UUID
    movement_type: str
    currency: str
    amount_original: Decimal
    payment_method: str
    movement_date: date


class TreasuryMovementRead(TreasuryMovementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    status: str
