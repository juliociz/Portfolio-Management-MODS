"""
Pipeline V1 :
sentiment FinBERT + momentum -> score global -> allocation discrète.
"""

import pandas as pd

# On va chercher le fichier config
import sys
import os
# Remonte de 3 niveaux pour atteindre le dossier principal (Portfolio-Management-MODS)
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.append(root_path)

from config import INITIAL_CAPITAL, TICKERS
from portfolio_manag.momentum.momentum import compute_momentum
from portfolio_manag.portfolio.allocator import discrete_allocation
from portfolio_manag.portfolio.scorer import compute_global_score


ALLOCATION_DATE = "2026-06-03"
MOMENTUM_WINDOWS = [1, 3]

SENTIMENT_PATH = "data_output/sentiment_scores.csv"
PRICES_PATH = "data_output/prices_alphavantage.csv"


def run_pipeline() -> None:
    sentiment = pd.read_csv(SENTIMENT_PATH)

    prices = pd.read_csv(
        PRICES_PATH,
        index_col="date",
        parse_dates=True,
    )

    prices = prices.loc[:ALLOCATION_DATE, TICKERS]

    if prices.empty:
        raise RuntimeError(
            f"Aucun prix disponible avant le {ALLOCATION_DATE}."
        )

    momentum = compute_momentum(
        prices,
        windows=MOMENTUM_WINDOWS,
    )

    scores = compute_global_score(
        sentiment,
        momentum,
    )

    latest_prices = prices.iloc[-1]

    allocation, leftover = discrete_allocation(
        scores,
        latest_prices,
        capital=INITIAL_CAPITAL,
    )

    print("\n=== Momentum ===")
    print(momentum.to_string(index=False))

    print("\n=== Scores globaux et poids ===")
    print(scores.to_string(index=False))

    print(f"\n=== Prix au {latest_prices.name.date()} ===")
    print(latest_prices.to_string())

    print("\n=== Allocation discrète ===")
    for ticker, quantity in allocation.items():
        print(f"{ticker}: {quantity} actions")

    print(f"\nCash restant : {leftover:.2f} $")


if __name__ == "__main__":
    run_pipeline()