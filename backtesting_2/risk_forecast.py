"""
risk_forecast.py

Transforme les signaux FinBERT + momentum en entrées pour PyPortfolioOpt :
  - mu ajusté par les scores globaux ;
  - S Ledoit-Wolf, éventuellement ajustée par multiplicateurs de risque.

Hypothèse V1 :
  mu_adjusted_i = mu_historical_i + SIGNAL_STRENGTH * global_score_i

Hypothèse V2 optionnelle :
  signal négatif → risque spécifique augmenté.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    SIGNAL_STRENGTH,
    RISK_LAMBDA,
    FREQUENCY,
)

logger = logging.getLogger(__name__)


def build_forecast_inputs(
    train_prices: pd.DataFrame,
    global_scores_df: pd.DataFrame,
    adjust_covariance: bool = False,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Calcule mu ajusté et S à partir des prix d'entraînement et des scores globaux.

    Retour :
        mu_adjusted : pd.Series
        S           : pd.DataFrame
    """
    from pypfopt.expected_returns import mean_historical_return
    from pypfopt.risk_models import CovarianceShrinkage

    clean_prices = train_prices.reindex(columns=TICKERS).ffill().dropna(how="all")
    clean_prices = clean_prices.dropna(axis=1, how="all")

    if len(clean_prices) < 30:
        raise ValueError(f"Historique de prix insuffisant pour PyPortfolioOpt : {len(clean_prices)} lignes.")

    mu_hist = mean_historical_return(
        clean_prices,
        compounding=True,
        frequency=FREQUENCY,
    )

    scores = global_scores_df.set_index("ticker")["global_score"]
    scores = scores.reindex(mu_hist.index).fillna(0.0)

    mu_adjusted = mu_hist + SIGNAL_STRENGTH * scores
    mu_adjusted.name = "mu_adjusted"

    S = CovarianceShrinkage(clean_prices, frequency=FREQUENCY).ledoit_wolf()

    if adjust_covariance:
        S = _adjust_covariance(S, scores)

    return mu_adjusted, S


def _adjust_covariance(S: pd.DataFrame, scores: pd.Series) -> pd.DataFrame:
    """
    Amplifie la covariance des actifs ayant un signal négatif.

    risk_multiplier_i = 1 + RISK_LAMBDA * max(0, -global_score_i)
    S_adjusted[i,j]  = S[i,j] * risk_multiplier_i * risk_multiplier_j
    """
    multipliers = pd.Series(
        {
            ticker: 1.0 + RISK_LAMBDA * max(0.0, -float(scores.get(ticker, 0.0)))
            for ticker in S.index
        },
        dtype=float,
    )

    M = np.outer(multipliers.values, multipliers.values)
    S_adj = pd.DataFrame(S.values * M, index=S.index, columns=S.columns)

    logger.debug("Multiplicateurs de risque : %s", multipliers.round(3).to_dict())
    return S_adj
