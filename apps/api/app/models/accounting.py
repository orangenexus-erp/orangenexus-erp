from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TenantMixin, UUIDPrimaryKeyMixin


class ChartOfAccount(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "chart_of_accounts"

    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_type: Mapped[str] = mapped_column(String(15), nullable=False)
    nature: Mapped[str] = mapped_column(String(7), nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    allows_movement: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CostCenter(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "cost_centers"

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class JournalEntry(UUIDPrimaryKeyMixin, TenantMixin, Base):
    __tablename__ = "journal_entries"

    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    entry_number: Mapped[str] = mapped_column(String(20), nullable=False)
    accounting_date: Mapped[date] = mapped_column(Date, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(12), nullable=False)
    source_module: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source_document_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="DRAFT")
    reversed_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)


class JournalEntryLine(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "journal_entry_lines"

    journal_entry_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=False)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("cost_centers.id"))
    original_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    exchange_rate_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("exchange_rates.id"))
    exchange_rate_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(7), nullable=False)
    line_description: Mapped[Optional[str]] = mapped_column(Text)


class IntegrationRule(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "integration_rules"

    event: Mapped[str] = mapped_column(String(50), nullable=False)
    debit_account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    credit_account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    amount_formula: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
