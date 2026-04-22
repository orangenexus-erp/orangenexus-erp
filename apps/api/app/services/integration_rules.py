from decimal import Decimal

from app.models.accounting import IntegrationRule


class IntegrationRulesEngine:
    """Motor base para procesar reglas de integración contable."""

    @staticmethod
    def resolve_amount(formula: str, payload: dict) -> Decimal:
        value = payload.get(formula, 0)
        return Decimal(str(value))

    async def get_rules_for_event(self, db, tenant_id, event: str) -> list[IntegrationRule]:
        result = await db.execute(
            IntegrationRule.__table__.select()
            .where(IntegrationRule.tenant_id == tenant_id)
            .where(IntegrationRule.event == event)
            .where(IntegrationRule.is_active.is_(True))
            .order_by(IntegrationRule.priority.asc())
        )
        return [IntegrationRule(**row._mapping) for row in result]
