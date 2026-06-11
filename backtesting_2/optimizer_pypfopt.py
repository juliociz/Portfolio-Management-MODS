"""
optimizer_pypfopt.py

Appelle PyPortfolioOpt pour produire des poids continus optimisés.

Fallback hiérarchique :
  1. max_sharpe ;
  2. min_volatility ;
  3. equal-weight.
"""

from __future__ import annotations

import logging

import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    WEIGHT_BOUNDS,
    RISK_FREE_RATE,
)

logger = logging.getLogger(__name__)


def optimize_with_pypfopt(
    mu: pd.Series,
    S: pd.DataFrame,
) -> dict[str, float]:
    """
    Optimise les poids avec PyPortfolioOpt.

    Retour :
        dictionnaire {ticker: poids} avec somme proche de 1.
    """
    from pypfopt.efficient_frontier import EfficientFrontier

    valid_tickers = [t for t in TICKERS if t in mu.index and t in S.index]
    if not valid_tickers:
        return _equal_weight()

    mu = mu.reindex(valid_tickers)
    S = S.reindex(index=valid_tickers, columns=valid_tickers)

    try:
        ef = EfficientFrontier(mu, S, weight_bounds=WEIGHT_BOUNDS)
        ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
        weights = dict(ef.clean_weights())
        logger.debug("max_sharpe réussi : %s", _fmt(weights))
        return _complete_weights(weights)
    except Exception as exc:
        logger.warning("max_sharpe échoué (%s). Tentative min_volatility.", exc)

    try:
        ef = EfficientFrontier(mu, S, weight_bounds=WEIGHT_BOUNDS)
        ef.min_volatility()
        weights = dict(ef.clean_weights())
        logger.warning("Fallback min_volatility utilisé : %s", _fmt(weights))
        return _complete_weights(weights)
    except Exception as exc:
        logger.warning("min_volatility échoué (%s). Fallback equal-weight.", exc)

    return _equal_weight()


def _complete_weights(weights: dict[str, float]) -> dict[str, float]:
    completed = {ticker: float(weights.get(ticker, 0.0)) for ticker in TICKERS}
    total = sum(completed.values())
    if total <= 0:
        return _equal_weight()
    return {ticker: completed[ticker] / total for ticker in TICKERS}


def _equal_weight() -> dict[str, float]:
    eq_weight = 1.0 / len(TICKERS)
    weights = {ticker: eq_weight for ticker in TICKERS}
    logger.warning("Fallback equal-weight : %s", _fmt(weights))
    return weights


def _fmt(weights: dict) -> str:
    return " | ".join(f"{ticker}={float(weights.get(ticker, 0.0)):.3f}" for ticker in TICKERS)
