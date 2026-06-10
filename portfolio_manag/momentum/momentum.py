# src/momentum/momentum.py
"""
Module de calcul du momentum.
Responsable : [camarade à assigner]

Le momentum mesure la performance récente d'une action sur plusieurs fenêtres
temporelles, puis combine ces mesures en un score normalisé.
"""

import pandas as pd
import numpy as np
from config import TICKERS, MOMENTUM_WINDOWS


def compute_momentum(prices: pd.DataFrame, windows: list = MOMENTUM_WINDOWS) -> pd.DataFrame:
    """
    Calcule le momentum pour chaque ticker sur plusieurs fenêtres temporelles.

    Args:
        prices:  DataFrame (index=date, colonnes=tickers) — sortie de fetch_prices.py
        windows: liste de fenêtres en mois, ex: [1, 3, 6]

    Returns:
        DataFrame avec colonnes : ticker | mom_1m | mom_3m | mom_6m | momentum_score
    """
    results = {}

    for window in windows:
        # Nombre de jours de trading approximatif
        trading_days = window * 21
        # Rendement sur la fenêtre = (prix_fin / prix_début) - 1
        returns = prices.pct_change(periods=trading_days).iloc[-1]
        results[f"mom_{window}m"] = returns

    df = pd.DataFrame(results)
    df.index.name = "ticker"
    df = df.reset_index()

    # Score de momentum = moyenne des rendements sur toutes les fenêtres
    mom_cols = [f"mom_{w}m" for w in windows]
    df["momentum_score"] = df[mom_cols].mean(axis=1)

    # Normalisation entre -1 et +1 (min-max sur les tickers)
    min_val = df["momentum_score"].min()
    max_val = df["momentum_score"].max()
    if max_val != min_val:
        df["momentum_score"] = 2 * (df["momentum_score"] - min_val) / (max_val - min_val) - 1
    else:
        df["momentum_score"] = 0.0

    df["momentum_score"] = df["momentum_score"].round(4)

    return df.sort_values("momentum_score", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    prices = pd.read_csv(
        "data_output/prices_alphavantage.csv",
        index_col="date",
        parse_dates=True,
    )

    prices = prices.loc[:"2026-06-03"]

    df = compute_momentum(
        prices,
        windows=[1, 3],
    )

    print(df.to_string(index=False))
