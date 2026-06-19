"""
Chargement des prix pour le backtest.

On télécharge les prix une seule fois pour toute la période, avec une marge avant
le début du backtest afin de calculer le momentum 1 mois / 3 mois.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from backtesting.config_backtest import TICKERS


def load_backtest_prices(
    start: str,
    end: str,
    tickers: list[str] = TICKERS,
    lookback_days: int = 110,
    cache_path: str | Path | None = "backtesting/data_output/prices_backtest.csv",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Charge les prix de clôture ajustés pour le backtest.

    Args:
        start: début du backtest au format YYYY-MM-DD.
        end: fin du backtest au format YYYY-MM-DD.
        lookback_days: marge avant start pour calculer le momentum.
        cache_path: CSV de cache optionnel.
        use_cache: si True, réutilise le cache s'il existe.

    Returns:
        DataFrame indexé par date, colonnes = tickers.
    """
    cache = Path(cache_path) if cache_path else None
    if use_cache and cache and cache.exists():
        prices = pd.read_csv(cache, index_col="date", parse_dates=True)
        return prices[tickers]

    start_dt = datetime.strptime(start, "%Y-%m-%d").date() - timedelta(days=lookback_days)
    end_dt = datetime.strptime(end, "%Y-%m-%d").date() + timedelta(days=1)  # yfinance end exclusif

    raw = yf.download(
        tickers,
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise RuntimeError("Aucun prix téléchargé depuis yfinance.")

    prices = raw["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    prices = prices.dropna(how="all")
    prices.columns.name = None
    prices.index.name = "date"
    prices = prices[tickers]

    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        prices.to_csv(cache)

    return prices


def get_latest_prices(prices: pd.DataFrame, day: str | pd.Timestamp) -> pd.Series:
    """
    Retourne les derniers prix connus à la date day incluse.

    Si day n'est pas un jour de marché, on prend la dernière clôture disponible avant day.
    """
    day_ts = pd.Timestamp(day)
    available = prices.loc[prices.index <= day_ts]
    if available.empty:
        raise ValueError(f"Aucun prix disponible avant ou à la date {day_ts.date()}.")
    latest = available.iloc[-1]
    if latest.isna().any():
        missing = latest[latest.isna()].index.tolist()
        raise ValueError(f"Prix manquants à {day_ts.date()} pour : {missing}")
    return latest
