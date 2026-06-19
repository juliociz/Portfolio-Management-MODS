"""
signals.py

Calcule le momentum et fusionne sentiment + momentum en un score global.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    SENTIMENT_WEIGHT,
    MOMENTUM_WEIGHT,
    MOMENTUM_WINDOWS,
    TRADING_DAYS_PER_MONTH,
)

logger = logging.getLogger(__name__)


def compute_daily_momentum(
    train_prices: pd.DataFrame,
    as_of: pd.Timestamp,
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Calcule le score de momentum pour chaque ticker à la date as_of.

    train_prices : DataFrame de prix ajustés, ne contenant que les données
                   disponibles jusqu'à as_of.
    windows      : fenêtres en mois, ex. [1, 3]

    Retour :
        ticker | mom_1m | mom_3m | ... | momentum_score
    """
    if windows is None:
        windows = MOMENTUM_WINDOWS

    available = train_prices.loc[:as_of].dropna(how="all")
    if available.empty:
        logger.warning("Pas de prix disponibles jusqu'à %s.", as_of)
        return _neutral_momentum(windows)

    rows = []
    for ticker in TICKERS:
        series = available[ticker].dropna() if ticker in available.columns else pd.Series(dtype=float)
        row = {"ticker": ticker}
        window_returns = []

        for w in windows:
            lag = w * TRADING_DAYS_PER_MONTH
            col = f"mom_{w}m"
            if len(series) > lag:
                price_today = float(series.iloc[-1])
                price_past = float(series.iloc[-(lag + 1)])
                ret = price_today / price_past - 1.0
            else:
                ret = 0.0
            row[col] = round(ret, 6)
            window_returns.append(ret)

        row["momentum_raw"] = float(np.mean(window_returns)) if window_returns else 0.0
        rows.append(row)

    df = pd.DataFrame(rows)

    raw = df["momentum_raw"]
    r_min, r_max = raw.min(), raw.max()
    if r_max - r_min < 1e-10:
        df["momentum_score"] = 0.0
    else:
        df["momentum_score"] = 2.0 * (raw - r_min) / (r_max - r_min) - 1.0

    df["momentum_score"] = df["momentum_score"].round(6)
    return df.drop(columns=["momentum_raw"])


def _neutral_momentum(windows: list[int] | None = None) -> pd.DataFrame:
    if windows is None:
        windows = MOMENTUM_WINDOWS
    rows = []
    for ticker in TICKERS:
        row = {"ticker": ticker}
        for w in windows:
            row[f"mom_{w}m"] = 0.0
        row["momentum_score"] = 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def compute_global_scores(
    sentiment_df: pd.DataFrame,
    momentum_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Fusionne sentiment et momentum en un score global pondéré.

    Retour :
        ticker | sentiment_score | momentum_score | global_score
    """
    sent = sentiment_df.set_index("ticker")["sentiment_score"]
    mom = momentum_df.set_index("ticker")["momentum_score"]

    rows = []
    for ticker in TICKERS:
        s = float(sent.get(ticker, 0.0))
        m = float(mom.get(ticker, 0.0))
        g = SENTIMENT_WEIGHT * s + MOMENTUM_WEIGHT * m
        rows.append(
            {
                "ticker": ticker,
                "sentiment_score": round(s, 6),
                "momentum_score": round(m, 6),
                "global_score": round(g, 6),
            }
        )

    return pd.DataFrame(rows)
