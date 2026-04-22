"""006_indexes_and_rls"""

from alembic import op

revision = "006_indexes_and_rls"
down_revision = "005_purchases"
branch_labels = None
depends_on = None

TENANT_TABLES = [
    "branches",
    "roles",
    "users",
    "chart_of_accounts",
    "cost_centers",
    "journal_entries",
    "integration_rules",
    "customers",
    "services",
    "sales_documents",
    "bank_accounts",
    "treasury_movements",
    "suppliers",
    "purchase_documents",
    "tax_withholdings",
]


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION current_tenant_id()
        RETURNS UUID
        LANGUAGE SQL STABLE
        AS $$
            SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid;
        $$;
        """
    )
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_policy ON {table} USING (tenant_id = current_tenant_id())"
        )
        op.execute(
            f"CREATE POLICY {table}_tenant_insert_policy ON {table} FOR INSERT WITH CHECK (tenant_id = current_tenant_id())"
        )

    op.execute("CREATE INDEX idx_users_tenant ON users (tenant_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_sales_documents_tenant ON sales_documents (tenant_id)")
    op.execute("CREATE INDEX idx_purchase_documents_tenant ON purchase_documents (tenant_id)")
    op.execute("CREATE INDEX idx_journal_entries_tenant ON journal_entries (tenant_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_journal_entries_tenant")
    op.execute("DROP INDEX IF EXISTS idx_purchase_documents_tenant")
    op.execute("DROP INDEX IF EXISTS idx_sales_documents_tenant")
    op.execute("DROP INDEX IF EXISTS idx_users_tenant")
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_insert_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_policy ON {table}")
