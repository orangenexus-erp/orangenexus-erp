from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TenantMixin, UUIDPrimaryKeyMixin


class BankAccount(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "bank_accounts"

    branch_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id"))
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="VES")
    ledger_account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TreasuryMovement(UUIDPrimaryKeyMixin, TenantMixin, AuditMixin, Base):
    __tablename__ = "treasury_movements"

    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    bank_account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    source_document_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    movement_type: Mapped[str] = mapped_column(String(15), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    amount_original: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    exchange_rate_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("exchange_rates.id"))
    exchange_rate_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    amount_ves: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    fx_gain_loss: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(30))
    movement_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(15), default="PENDING")
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))
