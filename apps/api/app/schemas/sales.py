from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    legal_name: str
    tax_id: str


class CustomerRead(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class ServiceCreate(BaseModel):
    code: str
    name: str
    unit_price_usd: Decimal = Decimal("0")
    unit_price_ves: Decimal = Decimal("0")


class ServiceRead(ServiceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class SalesDocumentCreate(BaseModel):
    branch_id: UUID
    customer_id: UUID
    document_type: str
    document_number: str
    issue_date: date
    currency: str = "USD"
    subtotal_usd: Decimal = Decimal("0")
    subtotal_ves: Decimal = Decimal("0")
    tax_amount_usd: Decimal = Decimal("0")
    tax_amount_ves: Decimal = Decimal("0")
    igtf_amount_usd: Decimal = Decimal("0")
    igtf_amount_ves: Decimal = Decimal("0")
    total_usd: Decimal = Decimal("0")
    total_ves: Decimal = Decimal("0")


class SalesDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    status: str
    total_usd: Decimal
    total_ves: Decimal
