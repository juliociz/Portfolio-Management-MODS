"""
prices_backtest.py

Charge ou télécharge les prix ajustés de clôture pour le backtest.
Supporte Yahoo Finance par défaut et Alpha Vantage en option.

Ce module est autonome et n'utilise aucun module de prix du reste du repository.
"""

from __future__ import annotations

import logging
import os
import time

import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    PRICES_CSV,
    PRICE_START,
    PRICE_END,
    PRICE_SOURCE,
)

logger = logging.getLogger(__name__)


def _fetch_alphavantage(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """
    Télécharge les prix via Alpha Vantage TIME_SERIES_DAILY_ADJUSTED.

    Attention : selon les conditions Alpha Vantage, certains endpoints ou
    paramètres peuvent être limités. Yahoo reste le fallback recommandé.
    """
    import requests

    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise EnvironmentError("ALPHAVANTAGE_API_KEY absent dans l'environnement.")

    frames = {}
    for i, ticker in enumerate(tickers):
        if i > 0:
            time.sleep(15)

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": ticker,
            "outputsize": "full",
            "apikey": api_key,
        }
        resp = requests.get("https://www.alphavantage.co/query", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        if "Note" in payload:
            raise RuntimeError(f"Limite Alpha Vantage atteinte : {payload['Note']}")
        if "Information" in payload:
            raise RuntimeError(f"Réponse Alpha Vantage : {payload['Information']}")
        if "Error Message" in payload:
            raise RuntimeError(f"Ticker invalide {ticker} : {payload['Error Message']}")

        data = payload.get("Time Series (Daily)", {})
        if not data:
            raise RuntimeError(f"Aucune donnée Alpha Vantage pour {ticker}.")

        series = {
            pd.Timestamp(d): float(v["5. adjusted close"])
            for d, v in data.items()
        }
        frames[ticker] = pd.Series(series, name=ticker).sort_index()
        logger.info("Alpha Vantage — %s : %s jours téléchargés.", ticker, len(series))

    prices = pd.DataFrame(frames)
    prices.index.name = "date"
    return prices.loc[start:end]


def _fetch_yahoo(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Télécharge les prix via yfinance."""
    import yfinance as yf

    logger.info("Utilisation de Yahoo Finance pour les prix.")
    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise RuntimeError("Yahoo Finance n'a retourné aucun prix.")

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    prices.index.name = "date"
    prices = prices.reindex(columns=tickers)
    return prices.dropna(how="all")


def load_prices(
    start: str = PRICE_START,
    end: str = PRICE_END,
    use_cache: bool = True,
    source: str = PRICE_SOURCE,
) -> pd.DataFrame:
    """
    Retourne un DataFrame de prix ajustés (index=date, colonnes=tickers).

    Ordre :
      1. cache CSV si disponible ;
      2. source demandée ;
      3. fallback Yahoo si Alpha Vantage échoue.
    """
    if use_cache and PRICES_CSV.exists():
        logger.info("Cache trouvé : %s", PRICES_CSV)
        prices = pd.read_csv(PRICES_CSV, parse_dates=["date"], index_col="date")
        prices.index = pd.to_datetime(prices.index)
        missing_cols = [t for t in TICKERS if t not in prices.columns]
        if not missing_cols:
            return prices.reindex(columns=TICKERS)

    if source == "alphavantage":
        try:
            prices = _fetch_alphavantage(TICKERS, start, end)
        except Exception as exc:
            logger.warning("Alpha Vantage indisponible (%s). Fallback Yahoo Finance.", exc)
            prices = _fetch_yahoo(TICKERS, start, end)
    else:
        prices = _fetch_yahoo(TICKERS, start, end)

    PRICES_CSV.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(PRICES_CSV)
    logger.info("Prix sauvegardés dans %s", PRICES_CSV)
    return prices.reindex(columns=TICKERS)


def get_train_prices(prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """
    Retourne les prix disponibles jusqu'à as_of inclus.
    """
    train = prices.loc[:as_of].dropna(how="all")
    if train.empty:
        raise ValueError(f"Aucun prix disponible avant {as_of}.")
    return train.reindex(columns=TICKERS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    df = load_prices(use_cache=False)
    print(df.tail())
