"""
Construction des signaux journaliers du backtest.

Pour une date J :
    sentiment J depuis alphavantage_merged_YYYYMMDD.json
    momentum J depuis les prix disponibles jusqu'à J
    score global et poids cibles via compute_global_score()
"""
from __future__ import annotations

import pandas as pd

from portfolio_manag.momentum.momentum import compute_momentum
from portfolio_manag.portfolio.scorer import compute_global_score

from backtesting.config_backtest import MOMENTUM_WINDOWS
from backtesting.sentiment_backtest import compute_daily_sentiment


def compute_daily_signal(
    json_path: str,
    prices: pd.DataFrame,
    day: str,
    momentum_windows: list[int] = MOMENTUM_WINDOWS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Calcule sentiment, momentum et scores globaux pour une journée.

    Returns:
        sentiment_df, momentum_df, scores_df
    """
    sentiment_df = compute_daily_sentiment(json_path, day=day)

    prices_until_day = prices.loc[prices.index <= pd.Timestamp(day)]
    if prices_until_day.empty:
        raise ValueError(f"Aucun prix disponible avant {day}.")

    momentum_df = compute_momentum(prices_until_day, windows=momentum_windows)
    momentum_df.insert(0, "date", day)

    scores_df = compute_global_score(sentiment_df, momentum_df)
    scores_df.insert(0, "date", day)

    return sentiment_df, momentum_df, scores_df
