"""001_extensions_and_core"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_extensions_and_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute(
        """
        CREATE TABLE tenants (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(100) NOT NULL,
            tax_id VARCHAR(20) NOT NULL UNIQUE,
            local_currency VARCHAR(3) NOT NULL DEFAULT 'VES',
            functional_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            fiscal_config JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        """
        CREATE TABLE branches (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            name VARCHAR(100) NOT NULL,
            code VARCHAR(10) NOT NULL,
            fiscal_address TEXT,
            control_number_seq BIGINT NOT NULL DEFAULT 0,
            invoice_number_seq BIGINT NOT NULL DEFAULT 0,
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
        CREATE TABLE roles (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            name VARCHAR(50) NOT NULL,
            level INT NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, name)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE permissions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            role_id UUID NOT NULL REFERENCES roles(id),
            module VARCHAR(50) NOT NULL,
            action VARCHAR(50) NOT NULL,
            allowed BOOLEAN NOT NULL DEFAULT true,
            UNIQUE(role_id, module, action)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            branch_id UUID NOT NULL REFERENCES branches(id),
            role_id UUID NOT NULL REFERENCES roles(id),
            email VARCHAR(150) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            last_login_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            deleted_at TIMESTAMPTZ,
            UNIQUE(tenant_id, email)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE exchange_rates (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            source_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            target_currency VARCHAR(3) NOT NULL DEFAULT 'VES',
            rate NUMERIC(18,6) NOT NULL,
            source VARCHAR(10) NOT NULL DEFAULT 'BCV',
            effective_date DATE NOT NULL,
            is_fallback BOOLEAN NOT NULL DEFAULT false,
            captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(source_currency, target_currency, effective_date)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE audit_log (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL,
            user_id UUID,
            table_name VARCHAR(60) NOT NULL,
            record_id UUID NOT NULL,
            action VARCHAR(20) NOT NULL,
            old_data JSONB,
            new_data JSONB,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE refresh_tokens (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id),
            token TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP TABLE IF EXISTS exchange_rates")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS permissions")
    op.execute("DROP TABLE IF EXISTS roles")
    op.execute("DROP TABLE IF EXISTS branches")
    op.execute("DROP TABLE IF EXISTS tenants")
