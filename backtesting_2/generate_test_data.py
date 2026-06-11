"""
generate_test_data.py

Génère des fichiers JSON de test pour valider le pipeline sans avoir les vrais
fichiers AlphaVantage journaliers.

Produit des fichiers :
    data_input/alphavantage_merged_20260501.json
    data_input/alphavantage_merged_20260504.json
    ...

Usage :
    python -m backtesting_2.generate_test_data
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from backtesting_2.config_backtest import DATA_INPUT, TICKERS

HEADLINES = {
    "TSLA": [
        "Tesla reports record quarterly deliveries, beating analyst estimates.",
        "Tesla faces regulatory scrutiny over autopilot safety concerns.",
        "Tesla expands Gigafactory capacity ahead of Model Y refresh.",
        "Tesla shares slide as competition intensifies from Chinese EV makers.",
        "Tesla cybertruck deliveries ramp up faster than expected.",
    ],
    "NKE": [
        "Nike quarterly earnings top forecasts on strong DTC channel growth.",
        "Nike shares fall after CEO warns of slowing demand in North America.",
        "Nike digital sales accelerate, driving margin expansion.",
        "Dow up on gains for shares of Home Depot and Nike.",
        "Nike faces backlash over labor practices in Asian factories.",
    ],
    "TGT": [
        "Target reports better-than-expected comparable store sales.",
        "Target expands same-day delivery to new markets.",
        "Target stock rises after raising full-year guidance.",
        "Target faces headwinds from consumer trade-down.",
        "Target cautious outlook disappoints investors despite solid quarter.",
    ],
    "DIS": [
        "Disney streaming division turns profitable for first time.",
        "Disney announces new theme park expansion in Asia.",
        "Disney box office hit drives subscriber growth on Disney+.",
        "Disney faces investor pressure over content spending levels.",
        "Disney parks record attendance over spring break period.",
    ],
    "SBUX": [
        "Starbucks reports comparable store sales growth driven by mobile orders.",
        "Starbucks faces union organizing efforts at new locations.",
        "Starbucks new CEO unveils plan to simplify menu and speed service.",
        "Starbucks shares dip after China same-store sales disappoint.",
        "Starbucks loyalty program engagement hits all-time high.",
    ],
}


def get_weekdays_may_2026() -> list[date]:
    days = []
    d = date(2026, 5, 1)
    while d.month == 5:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def generate_test_files(output_dir: Path = DATA_INPUT, seed: int = 42) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    random.seed(seed)

    days = get_weekdays_may_2026()
    print(f"Génération de {len(days)} fichiers JSON dans {output_dir}/")

    for day in days:
        data = {}
        for ticker in TICKERS:
            n = random.randint(5, 10)
            data[ticker] = random.choices(HEADLINES[ticker], k=n)

        filename = output_dir / f"alphavantage_merged_{day.strftime('%Y%m%d')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"{len(days)} fichiers générés : {days[0]} → {days[-1]}")


if __name__ == "__main__":
    generate_test_files()
