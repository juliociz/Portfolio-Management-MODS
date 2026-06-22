"""
optimizer_pypfopt.py

Appelle PyPortfolioOpt pour produire des poids continus optimisés.

Fallback hiérarchique :
  1. max_quadratic_utility  ← objectif principal : utilise mu_adjusted directement,
                              sans dépendre du risk_free_rate → le signal FinBERT+Momentum
                              influence réellement les poids à chaque itération ;
  2. min_volatility         ← fallback si l'utilité quadratique échoue ;
  3. equal-weight           ← dernier recours.

Pourquoi max_quadratic_utility plutôt que max_sharpe ?
  max_sharpe requiert qu'au moins un actif ait mu > risk_free_rate, ce qui
  peut échouer selon l'environnement de taux.  max_quadratic_utility maximise
  mu^T w - (risk_aversion/2) * w^T S w sans ce prérequis, et intègre
  nativement mu_adjusted dans la solution optimale.
"""

from __future__ import annotations

import logging

import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    WEIGHT_BOUNDS,
    RISK_AVERSION,
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

    # ── 1. max_quadratic_utility ──────────────────────────────────────────────
    # Maximise mu^T w - (risk_aversion/2) * w^T S w
    # Utilise mu_adjusted directement → le signal FinBERT+Momentum a un impact réel.
    try:
        ef = EfficientFrontier(mu, S, weight_bounds=WEIGHT_BOUNDS)
        ef.max_quadratic_utility(risk_aversion=RISK_AVERSION)
        weights = dict(ef.clean_weights())
        logger.info("max_quadratic_utility réussi : %s", _fmt(weights))
        return _complete_weights(weights)
    except Exception as exc:
        logger.warning("max_quadratic_utility échoué (%s). Tentative min_volatility.", exc)

    # ── 2. min_volatility ─────────────────────────────────────────────────────
    try:
        ef = EfficientFrontier(mu, S, weight_bounds=WEIGHT_BOUNDS)
        ef.min_volatility()
        weights = dict(ef.clean_weights())
        logger.warning("Fallback min_volatility utilisé : %s", _fmt(weights))
        return _complete_weights(weights)
    except Exception as exc:
        logger.warning("min_volatility échoué (%s). Fallback equal-weight.", exc)

    # ── 3. equal-weight ───────────────────────────────────────────────────────
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