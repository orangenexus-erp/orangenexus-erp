"""002_accounting"""

from alembic import op

revision = "002_accounting"
down_revision = "001_extensions_and_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chart_of_accounts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            account_code VARCHAR(20) NOT NULL,
            account_name VARCHAR(150) NOT NULL,
            account_type VARCHAR(15) NOT NULL,
            nature VARCHAR(7) NOT NULL,
            parent_id UUID REFERENCES chart_of_accounts(id),
            level INT NOT NULL,
            allows_movement BOOLEAN NOT NULL DEFAULT false,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, account_code)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE cost_centers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            branch_id UUID REFERENCES branches(id),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, code)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE journal_entries (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            branch_id UUID NOT NULL REFERENCES branches(id),
            entry_number VARCHAR(20) NOT NULL,
            accounting_date DATE NOT NULL,
            entry_type VARCHAR(12) NOT NULL,
            source_module VARCHAR(20),
            source_document_id UUID,
            description TEXT NOT NULL,
            status VARCHAR(15) NOT NULL DEFAULT 'DRAFT',
            reversed_by_id UUID REFERENCES journal_entries(id),
            created_by UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(tenant_id, entry_number)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE journal_entry_lines (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            journal_entry_id UUID NOT NULL REFERENCES journal_entries(id),
            account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
            cost_center_id UUID REFERENCES cost_centers(id),
            original_currency VARCHAR(3) NOT NULL,
            original_amount NUMERIC(18,2) NOT NULL,
            exchange_rate_id UUID REFERENCES exchange_rates(id),
            exchange_rate_value NUMERIC(18,6) NOT NULL,
            amount_ves NUMERIC(18,2) NOT NULL,
            amount_usd NUMERIC(18,2) NOT NULL,
            movement_type VARCHAR(7) NOT NULL,
            line_description TEXT
        )
        """
    )
    op.execute(
        """
        CREATE TABLE integration_rules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            event VARCHAR(50) NOT NULL,
            debit_account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
            credit_account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
            amount_formula VARCHAR(50) NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            priority INT NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, event, priority)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS integration_rules")
    op.execute("DROP TABLE IF EXISTS journal_entry_lines")
    op.execute("DROP TABLE IF EXISTS journal_entries")
    op.execute("DROP TABLE IF EXISTS cost_centers")
    op.execute("DROP TABLE IF EXISTS chart_of_accounts")
