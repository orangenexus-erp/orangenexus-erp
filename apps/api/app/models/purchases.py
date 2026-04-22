from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TenantMixin, UUIDPrimaryKeyMixin


class Supplier(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "suppliers"

    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(20), nullable=False)
    fiscal_address: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(String(150))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    supplier_type: Mapped[str] = mapped_column(String(20), default="ORDINARY")
    iva_withholding_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=75)
    islr_category: Mapped[Optional[str]] = mapped_column(String(10))
    islr_withholding_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    is_special_taxpayer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PurchaseDocument(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "purchase_documents"

    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(15), nullable=False)
    document_number: Mapped[str] = mapped_column(String(20), nullable=False)
    supplier_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    exchange_rate_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("exchange_rates.id"))
    exchange_rate_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    subtotal_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    subtotal_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    paid_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    paid_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    balance_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    balance_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    status: Mapped[str] = mapped_column(String(15), default="DRAFT")
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_document_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("purchase_documents.id"))
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)


class TaxWithholding(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "tax_withholdings"

    purchase_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("purchase_documents.id"), nullable=False)
    supplier_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    withholding_type: Mapped[str] = mapped_column(String(5), nullable=False)
    taxable_base_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    taxable_base_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    withholding_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    withheld_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    withheld_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    voucher_number: Mapped[str] = mapped_column(String(30), nullable=False)
    withholding_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="ISSUED")
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))
