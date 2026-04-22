"""003_sales"""

from alembic import op

revision = "003_sales"
down_revision = "002_accounting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE customers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            legal_name VARCHAR(200) NOT NULL,
            tax_id VARCHAR(20) NOT NULL,
            fiscal_address TEXT,
            email VARCHAR(150),
            phone VARCHAR(20),
            customer_type VARCHAR(20) NOT NULL DEFAULT 'ORDINARY',
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
        CREATE TABLE services (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR(20) NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            unit_price_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            unit_price_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            is_taxable BOOLEAN NOT NULL DEFAULT true,
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
        CREATE TABLE sales_documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            branch_id UUID NOT NULL REFERENCES branches(id),
            document_type VARCHAR(15) NOT NULL,
            document_number VARCHAR(20) NOT NULL,
            control_number VARCHAR(20),
            customer_id UUID NOT NULL REFERENCES customers(id),
            issue_date DATE NOT NULL,
            due_date DATE,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            exchange_rate_id UUID REFERENCES exchange_rates(id),
            exchange_rate_value NUMERIC(18,6) NOT NULL DEFAULT 1,
            subtotal_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            subtotal_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            tax_amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            tax_amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            igtf_amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            igtf_amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            total_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            total_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            paid_amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            paid_amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            balance_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            balance_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            status VARCHAR(15) NOT NULL DEFAULT 'DRAFT',
            annulled_by_doc_id UUID REFERENCES sales_documents(id),
            source_document_id UUID REFERENCES sales_documents(id),
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
        CREATE TABLE sales_document_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            sales_document_id UUID NOT NULL REFERENCES sales_documents(id),
            service_id UUID REFERENCES services(id),
            line_number INT NOT NULL,
            description VARCHAR(200) NOT NULL,
            quantity NUMERIC(18,4) NOT NULL,
            unit_price_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            unit_price_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            subtotal_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            subtotal_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            tax_rate NUMERIC(5,2) NOT NULL DEFAULT 16,
            tax_amount_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            tax_amount_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            total_usd NUMERIC(18,2) NOT NULL DEFAULT 0,
            total_ves NUMERIC(18,2) NOT NULL DEFAULT 0,
            UNIQUE(sales_document_id, line_number)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sales_document_items")
    op.execute("DROP TABLE IF EXISTS sales_documents")
    op.execute("DROP TABLE IF EXISTS services")
    op.execute("DROP TABLE IF EXISTS customers")
