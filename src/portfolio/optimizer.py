# src/portfolio/optimizer.py
"""
Module d'optimisation de portefeuille avec PyPortfolioOpt.
Responsable : [camarade à assigner]

V2 : intègre les scores globaux comme vues dans l'approche Black-Litterman.
"""

import pandas as pd
import numpy as np
from pypfopt import (
    EfficientFrontier,
    risk_models,
    expected_returns,
    BlackLittermanModel,
    black_litterman,
)
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from config import INITIAL_CAPITAL


# ========================
# V1 : Optimisation simple sous contrainte de risque
# ========================

def optimize_max_sharpe(prices: pd.DataFrame) -> dict:
    """
    Optimisation classique : maximisation du ratio de Sharpe.

    Args:
        prices: DataFrame (index=date, colonnes=tickers)

    Returns:
        dict {ticker: poids} avec les poids optimaux
    """
    mu  = expected_returns.mean_historical_return(prices)
    cov = risk_models.sample_cov(prices)

    ef = EfficientFrontier(mu, cov)
    ef.add_constraint(lambda w: w >= 0.05)   # poids min 5% par action
    ef.add_constraint(lambda w: w <= 0.40)   # poids max 40% par action
    weights = ef.max_sharpe()
    cleaned = ef.clean_weights()

    performance = ef.portfolio_performance(verbose=True)

    return {
        "weights":     dict(cleaned),
        "performance": {
            "expected_return": round(performance[0], 4),
            "volatility":      round(performance[1], 4),
            "sharpe_ratio":    round(performance[2], 4),
        }
    }


# ========================
# V2 : Black-Litterman avec signaux sentiment/momentum
# ========================

def optimize_black_litterman(
    prices: pd.DataFrame,
    global_scores: pd.DataFrame,
) -> dict:
    """
    Optimisation Black-Litterman : les scores sentiment+momentum
    sont utilisés comme vues (views) sur les rendements attendus.

    Args:
        prices:        DataFrame des prix (index=date, colonnes=tickers)
        global_scores: DataFrame avec colonnes [ticker, global_score, weight]
                       sortie de scorer.compute_global_score()

    Returns:
        dict {ticker: poids} avec les poids optimaux
    """
    tickers = list(prices.columns)

    # Matrice de covariance du marché
    cov_matrix  = risk_models.sample_cov(prices)

    # Capitalisation boursière (proxy : poids égaux ici, à améliorer avec vraie mcap)
    market_caps = {ticker: 1.0 for ticker in tickers}

    # Prior de marché (rendements implicites)
    delta         = black_litterman.market_implied_risk_aversion(prices[tickers[-1]])
    prior_returns = black_litterman.market_implied_prior_returns(market_caps, delta, cov_matrix)

    # Construction des vues à partir des scores globaux
    # Vue absolue : "AAPL va surperformer de X%" selon le score
    scores_map = dict(zip(global_scores["ticker"], global_scores["global_score"]))
    # Conversion score [-1, +1] → rendement attendu supplémentaire (±10%)
    viewdict = {ticker: score * 0.10 for ticker, score in scores_map.items() if ticker in tickers}

    # Modèle Black-Litterman
    bl = BlackLittermanModel(
        cov_matrix,
        pi=prior_returns,
        absolute_views=viewdict,
    )

    ret_bl  = bl.bl_returns()
    cov_bl  = bl.bl_cov()

    # Optimisation sur la frontière efficiente
    ef = EfficientFrontier(ret_bl, cov_bl)
    ef.add_constraint(lambda w: w >= 0.05)
    ef.add_constraint(lambda w: w <= 0.40)
    weights = ef.max_sharpe()
    cleaned = ef.clean_weights()

    performance = ef.portfolio_performance(verbose=True)

    return {
        "weights": dict(cleaned),
        "performance": {
            "expected_return": round(performance[0], 4),
            "volatility":      round(performance[1], 4),
            "sharpe_ratio":    round(performance[2], 4),
        }
    }


# ========================
# Allocation discrète (nb d'actions à acheter)
# ========================

def discrete_allocation(weights: dict, prices: pd.DataFrame, capital: float = INITIAL_CAPITAL):
    """
    Convertit des poids continus en nombre d'actions à acheter.

    Returns:
        allocation (dict {ticker: nb_actions}), leftover (cash restant)
    """
    latest_prices = get_latest_prices(prices)
    da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=capital)
    allocation, leftover = da.lp_portfolio()
    print(f"Capital restant non alloué : ${leftover:.2f}")
    return allocation, leftover


if __name__ == "__main__":
    from src.data.fetch_prices import load_prices
    prices = load_prices()
    result = optimize_max_sharpe(prices)
    print("Poids optimaux :", result["weights"])
    print("Performance    :", result["performance"])
