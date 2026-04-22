from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import httpx
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "postgresql://orangenexus:orangenexus@localhost:5432/orangenexus")


def fetch_bcv_rate() -> Decimal | None:
    response = httpx.get("https://www.bcv.org.ve/", timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    candidates = [elem.get_text(strip=True) for elem in soup.select("div,span,strong") if "USD" in elem.get_text()]

    for item in candidates:
        cleaned = item.replace("USD", "").replace("Bs", "").replace(".", "").replace(",", ".").strip()
        try:
            value = Decimal(cleaned)
            if value > 0:
                return value
        except Exception:
            continue
    return None


def fallback_rate(engine) -> Decimal | None:
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                SELECT rate
                FROM exchange_rates
                WHERE source_currency = 'USD' AND target_currency = 'VES'
                ORDER BY effective_date DESC
                LIMIT 1
                """
            )
        ).fetchone()
    return Decimal(str(result[0])) if result else None


def save_rate(rate: Decimal, is_fallback: bool = False):
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO exchange_rates (
                    source_currency, target_currency, rate, source, effective_date, is_fallback
                ) VALUES ('USD', 'VES', :rate, 'BCV', :effective_date, :is_fallback)
                ON CONFLICT (source_currency, target_currency, effective_date)
                DO UPDATE SET rate = EXCLUDED.rate, is_fallback = EXCLUDED.is_fallback, captured_at = now()
                """
            ),
            {"rate": str(rate), "effective_date": date.today(), "is_fallback": is_fallback},
        )


def run_job():
    engine = create_engine(DATABASE_URL)
    rate = fetch_bcv_rate()
    fallback = False
    if rate is None:
        rate = fallback_rate(engine)
        fallback = True

    if rate is None:
        raise RuntimeError("No se pudo obtener tasa BCV ni fallback")

    save_rate(rate, fallback)
    print(f"[fx-rate-bot] tasa guardada: {rate} fallback={fallback}")


def run_scheduler():
    scheduler = BlockingScheduler(timezone="America/Caracas")
    scheduler.add_job(run_job, "cron", hour=6, minute=0)
    scheduler.start()


if __name__ == "__main__":
    mode = os.getenv("FX_BOT_MODE", "once")
    if mode == "scheduler":
        run_scheduler()
    else:
        run_job()
