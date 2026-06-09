# src/portfolio/scorer.py
"""
Module de combinaison sentiment + momentum en un score global.
Ce score est utilisé pour pondérer les allocations du portefeuille.
"""

import pandas as pd
from config import SENTIMENT_WEIGHT, MOMENTUM_WEIGHT


def compute_global_score(
    sentiment_df: pd.DataFrame,
    momentum_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine les scores de sentiment et de momentum en un score global.

    Args:
        sentiment_df : DataFrame avec colonnes [ticker, sentiment_score]  ∈ [-1, +1]
        momentum_df  : DataFrame avec colonnes [ticker, momentum_score]   ∈ [-1, +1]

    Returns:
        DataFrame avec colonnes : ticker | sentiment_score | momentum_score | global_score | weight
        weight : allocation cible du portefeuille (somme = 1)
    """
    assert abs(SENTIMENT_WEIGHT + MOMENTUM_WEIGHT - 1.0) < 1e-9, \
        "SENTIMENT_WEIGHT + MOMENTUM_WEIGHT doit être égal à 1"

    # Fusion des deux DataFrames sur le ticker
    df = sentiment_df[["ticker", "sentiment_score"]].merge(
        momentum_df[["ticker", "momentum_score"]],
        on="ticker",
        how="inner",
    )

    # Score global pondéré
    df["global_score"] = (
        SENTIMENT_WEIGHT * df["sentiment_score"] +
        MOMENTUM_WEIGHT  * df["momentum_score"]
    ).round(4)

    # Conversion en poids de portefeuille (softmax pour garantir somme = 1 et poids > 0)
    import numpy as np
    scores = df["global_score"].values
    exp_scores = np.exp(scores - scores.max())   # soustraction pour stabilité numérique
    df["weight"] = (exp_scores / exp_scores.sum()).round(4)

    return df.sort_values("global_score", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    # Exemple minimal pour tester
    sentiment = pd.DataFrame({
        "ticker":          ["AAPL", "MSFT", "JPM", "XOM", "JNJ"],
        "sentiment_score": [0.45, 0.30, -0.10, 0.05, 0.20],
    })
    momentum = pd.DataFrame({
        "ticker":          ["AAPL", "MSFT", "JPM", "XOM", "JNJ"],
        "momentum_score":  [0.60, 0.50, -0.20, 0.10, 0.30],
    })
    df = compute_global_score(sentiment, momentum)
    print(df.to_string(index=False))
