"""Seed inicial para OrangeNexus ERP."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orangenexus:orangenexus@localhost:5432/orangenexus"


def run_seed():
    engine = create_engine(DATABASE_URL)
    tenant_id = uuid4()
    branch_id = uuid4()
    role_id = uuid4()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, name, tax_id, local_currency, functional_currency)
                VALUES (:id, :name, :tax_id, 'VES', 'USD')
                ON CONFLICT (tax_id) DO NOTHING
                """
            ),
            {"id": str(tenant_id), "name": "OrangeNexus Venezuela", "tax_id": "J-00000000-0"},
        )

        conn.execute(
            text(
                """
                INSERT INTO branches (id, tenant_id, name, code, fiscal_address)
                VALUES (:id, :tenant_id, :name, :code, :fiscal_address)
                ON CONFLICT (tenant_id, code) DO NOTHING
                """
            ),
            {
                "id": str(branch_id),
                "tenant_id": str(tenant_id),
                "name": "Sede Caracas",
                "code": "01",
                "fiscal_address": "Caracas, Venezuela",
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO roles (id, tenant_id, name, level, description)
                VALUES (:id, :tenant_id, :name, :level, :description)
                ON CONFLICT (tenant_id, name) DO NOTHING
                """
            ),
            {
                "id": str(role_id),
                "tenant_id": str(tenant_id),
                "name": "Admin",
                "level": 1,
                "description": "Administrador global",
            },
        )

    print(f"Seed aplicado @ {datetime.now().isoformat()}")


if __name__ == "__main__":
    run_seed()
