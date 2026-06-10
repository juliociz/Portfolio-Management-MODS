"""
Génère quelques fichiers JSON fictifs pour tester le pipeline sans les vraies données.

Usage :
    python -m backtesting.generate_test_data
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from backtesting.config_backtest import DATA_INPUT_DIR, TICKERS

HEADLINES = {
    "TSLA": [
        "Tesla reports stronger vehicle deliveries than analysts expected.",
        "Tesla faces pressure as EV competition intensifies.",
        "Elon Musk says Tesla energy storage demand remains robust.",
    ],
    "NKE": [
        "Nike shares rise after positive retail sales data.",
        "Nike warns of softer demand in North America.",
        "Nike launches new running shoe line to strong consumer interest.",
    ],
    "TGT": [
        "Target reports resilient consumer spending across core categories.",
        "Target shares dip after cautious guidance.",
        "Target expands same-day delivery capacity.",
    ],
    "DIS": [
        "Disney streaming business shows improving profitability.",
        "Disney parks attendance remains strong into summer season.",
        "Disney faces pressure from declining linear TV revenue.",
    ],
    "SBUX": [
        "Starbucks mobile orders support comparable store sales growth.",
        "Starbucks shares fall as China sales disappoint.",
        "Starbucks announces new turnaround plan focused on store operations.",
    ],
}


def business_days_may_2026() -> list[date]:
    days: list[date] = []
    current = date(2026, 5, 1)
    while current.month == 5:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def generate_test_data(output_dir: Path = DATA_INPUT_DIR, seed: int = 42) -> None:
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    for day in business_days_may_2026():
        payload = {
            ticker: random.choices(HEADLINES[ticker], k=random.randint(5, 10))
            for ticker in TICKERS
        }
        path = output_dir / f"alphavantage_merged_{day.strftime('%Y%m%d')}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Données de test générées dans : {output_dir}")


if __name__ == "__main__":
    generate_test_data()
