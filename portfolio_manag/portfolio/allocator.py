"""
Conversion des scores de momentum en poids de portefeuille.
"""

import pandas as pd


def momentum_to_weights(momentum_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertit les scores de momentum positifs en poids de portefeuille.

    Les scores négatifs sont ramenés à 0.
    Les poids finaux somment à 1.
    """
    required_columns = {"ticker", "momentum_score"}

    if not required_columns.issubset(momentum_df.columns):
        raise ValueError(
            "Le DataFrame doit contenir les colonnes "
            "'ticker' et 'momentum_score'."
        )

    result = momentum_df.copy()

    result["positive_score"] = result["momentum_score"].clip(lower=0)

    total_score = result["positive_score"].sum()

    if total_score <= 0:
        raise ValueError(
            "Aucun ticker n'a un momentum positif. "
            "Impossible de calculer une allocation."
        )

    result["weight"] = result["positive_score"] / total_score

    return result[
        ["ticker", "momentum_score", "weight"]
    ].sort_values("weight", ascending=False).reset_index(drop=True)

def discrete_allocation(
    weights_df: pd.DataFrame,
    latest_prices: pd.Series,
    capital: float,
) -> tuple[dict[str, int], float]:
    """
    Convertit les poids en nombre entier d'actions.

    Args:
        weights_df:
            DataFrame avec colonnes ticker et weight.
        latest_prices:
            Series indexée par ticker contenant le dernier prix.
        capital:
            Capital total disponible.

    Returns:
        allocation:
            Dictionnaire {ticker: nombre_d_actions}.
        leftover:
            Cash restant après achat.
    """
    required_columns = {"ticker", "weight"}

    if not required_columns.issubset(weights_df.columns):
        raise ValueError(
            "Le DataFrame doit contenir les colonnes "
            "'ticker' et 'weight'."
        )

    if capital <= 0:
        raise ValueError("Le capital doit être strictement positif.")

    allocation = {}
    invested_amount = 0.0

    for _, row in weights_df.iterrows():
        ticker = row["ticker"]
        weight = float(row["weight"])

        if ticker not in latest_prices.index:
            raise ValueError(
                f"Prix manquant pour le ticker {ticker}."
            )

        price = float(latest_prices[ticker])

        if price <= 0:
            raise ValueError(
                f"Prix invalide pour le ticker {ticker}: {price}"
            )

        budget = capital * weight
        quantity = int(budget // price)

        allocation[ticker] = quantity
        invested_amount += quantity * price

    leftover = capital - invested_amount

    return allocation, leftover
