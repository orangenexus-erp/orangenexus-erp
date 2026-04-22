from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SupplierCreate(BaseModel):
    legal_name: str
    tax_id: str
    supplier_type: str = "ORDINARY"


class SupplierRead(SupplierCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class PurchaseDocumentCreate(BaseModel):
    branch_id: UUID
    supplier_id: UUID
    document_type: str
    document_number: str
    issue_date: date
    currency: str = "USD"
    subtotal_usd: Decimal = Decimal("0")
    subtotal_ves: Decimal = Decimal("0")
    tax_amount_usd: Decimal = Decimal("0")
    tax_amount_ves: Decimal = Decimal("0")
    total_usd: Decimal = Decimal("0")
    total_ves: Decimal = Decimal("0")


class PurchaseDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    status: str


class TaxWithholdingCreate(BaseModel):
    purchase_document_id: UUID
    supplier_id: UUID
    withholding_type: str
    taxable_base_usd: Decimal
    taxable_base_ves: Decimal
    withholding_rate: Decimal
    withheld_amount_usd: Decimal
    withheld_amount_ves: Decimal
    voucher_number: str
    withholding_date: date


class TaxWithholdingRead(TaxWithholdingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    status: str
