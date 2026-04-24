from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, TenantMixin, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "customers"

    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(20), nullable=False)
    fiscal_address: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(String(150))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    customer_type: Mapped[str] = mapped_column(String(20), default="ORDINARY")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Service(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "services"

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    unit_price_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    unit_price_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SalesDocument(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "sales_documents"

    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(15), nullable=False)
    document_number: Mapped[str] = mapped_column(String(20), nullable=False)
    control_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    exchange_rate_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("exchange_rates.id"))
    exchange_rate_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    subtotal_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    subtotal_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    igtf_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    igtf_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    paid_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    paid_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    balance_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    balance_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    status: Mapped[str] = mapped_column(String(15), default="DRAFT")
    annulled_by_doc_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sales_documents.id"))
    source_document_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sales_documents.id"))
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    items: Mapped[list["SalesDocumentItem"]] = relationship(
        "SalesDocumentItem",
        back_populates="sales_document",
        cascade="all, delete-orphan",
    )


class SalesDocumentItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sales_document_items"

    sales_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sales_documents.id"), nullable=False)
    service_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("services.id"))
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    unit_price_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    subtotal_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    subtotal_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=16)
    tax_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    sales_document: Mapped[SalesDocument] = relationship("SalesDocument", back_populates="items")
