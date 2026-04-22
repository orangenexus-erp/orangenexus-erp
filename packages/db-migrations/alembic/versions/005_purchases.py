"""005_purchases"""

from alembic import op

revision = "005_purchases"
down_revision = "004_treasury"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE suppliers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            legal_name VARCHAR(200) NOT NULL,
            tax_id VARCHAR(20) NOT NULL,
            fiscal_address TEXT,
            email VARCHAR(150),
            phone VARCHAR(20),
            supplier_type VARCHAR(20) NOT NULL DEFAULT 'ORDINARY',
            iva_withholding_pct NUMERIC(5,2) NOT NULL DEFAULT 75,
            islr_category VARCHAR(10),
            islr_withholding_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
            is_special_taxpayer BOOLEAN NOT NULL DEFAULT false,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, tax_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE purchase_documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            branch_id UUID NOT NULL REFERENCES branches(id),
            document_type VARCHAR(15) NOT NULL,
            document_number VARCHAR(20) NOT NULL,
            supplier_id UUID NOT NULL REFERENCES suppliers(id),
            issue_date DATE NOT NULL,
            due_date DATE,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            exchange_rate_id UUID REFERENCES exchange_rates(id),
            exchange_rate_value NUMERIC(18,6) NOT NULL DEFAULT 1,
            subtotal_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            subtotal_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            tax_amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            tax_amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            total_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            total_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            paid_amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            paid_amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            balance_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            balance_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            status VARCHAR(15) NOT NULL DEFAULT 'DRAFT',
            approved_by UUID,
            approved_at TIMESTAMPTZ,
            source_document_id UUID REFERENCES purchase_documents(id),
            journal_entry_id UUID REFERENCES journal_entries(id),
            notes TEXT,
            created_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, branch_id, document_type, document_number)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE tax_withholdings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            purchase_document_id UUID NOT NULL REFERENCES purchase_documents(id),
            supplier_id UUID NOT NULL REFERENCES suppliers(id),
            withholding_type VARCHAR(5) NOT NULL,
            taxable_base_usd NUMERIC(18,2) NOT NULL,
            taxable_base_ves NUMERIC(18,2) NOT NULL,
            withholding_rate NUMERIC(5,2) NOT NULL,
            withheld_amount_usd NUMERIC(18,2) NOT NULL,
            withheld_amount_ves NUMERIC(18,2) NOT NULL,
            voucher_number VARCHAR(30) NOT NULL,
            withholding_date DATE NOT NULL,
            status VARCHAR(10) NOT NULL DEFAULT 'ISSUED',
            journal_entry_id UUID REFERENCES journal_entries(id),
            created_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, voucher_number)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tax_withholdings")
    op.execute("DROP TABLE IF EXISTS purchase_documents")
    op.execute("DROP TABLE IF EXISTS suppliers")
