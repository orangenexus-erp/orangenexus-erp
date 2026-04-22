from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import ExchangeRate


async def get_latest_rate(db: AsyncSession, source_currency: str = "USD", target_currency: str = "VES"):
    query = (
        select(ExchangeRate)
        .where(ExchangeRate.source_currency == source_currency)
        .where(ExchangeRate.target_currency == target_currency)
        .order_by(ExchangeRate.effective_date.desc())
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_today_rate(db: AsyncSession):
    query = (
        select(ExchangeRate)
        .where(ExchangeRate.source_currency == "USD")
        .where(ExchangeRate.target_currency == "VES")
        .where(ExchangeRate.effective_date == date.today())
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
