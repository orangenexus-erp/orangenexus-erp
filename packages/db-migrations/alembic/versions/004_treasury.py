"""004_treasury"""

from alembic import op

revision = "004_treasury"
down_revision = "003_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE bank_accounts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            branch_id UUID REFERENCES branches(id),
            bank_name VARCHAR(100) NOT NULL,
            account_number VARCHAR(30) NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT 'VES',
            ledger_account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
            current_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, account_number)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE treasury_movements (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            branch_id UUID NOT NULL REFERENCES branches(id),
            bank_account_id UUID NOT NULL REFERENCES bank_accounts(id),
            source_document_id UUID,
            movement_type VARCHAR(15) NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            amount_original NUMERIC(18,2) NOT NULL,
            exchange_rate_id UUID REFERENCES exchange_rates(id),
            exchange_rate_value NUMERIC(18,6) NOT NULL DEFAULT 1,
            amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            fx_gain_loss NUMERIC(18,2) NOT NULL DEFAULT 0,
            payment_method VARCHAR(50) NOT NULL,
            reference_number VARCHAR(30),
            movement_date DATE NOT NULL,
            description TEXT,
            status VARCHAR(15) NOT NULL DEFAULT 'PENDING',
            journal_entry_id UUID REFERENCES journal_entries(id),
            created_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS treasury_movements")
    op.execute("DROP TABLE IF EXISTS bank_accounts")
