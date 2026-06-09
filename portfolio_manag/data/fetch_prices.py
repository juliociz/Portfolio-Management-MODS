"""
Téléchargement et mise en cache des prix historiques depuis Yahoo Finance.
"""

import time
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import END_DATE, START_DATE, TICKERS


CACHE_PATH = Path("data_output/prices.csv")


def load_prices(
    tickers: list[str] = TICKERS,
    start: str = START_DATE,
    end: str = END_DATE,
    max_retries: int = 2,
    retry_delay: int = 15,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Charge les prix depuis le cache et télécharge uniquement
    les tickers manquants.
    """
    cached_prices = pd.DataFrame()

    if use_cache and CACHE_PATH.exists():
        cached_prices = pd.read_csv(
            CACHE_PATH,
            index_col="date",
            parse_dates=True,
        )

    missing_tickers = [
        ticker for ticker in tickers
        if ticker not in cached_prices.columns
    ]

    if not missing_tickers:
        return cached_prices[tickers]

    downloaded_series = []
    failed_tickers = []

    for ticker in missing_tickers:
        success = False

        for attempt in range(1, max_retries + 1):
            try:
                raw = yf.download(
                    ticker,
                    start=start,
                    end=end,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )

                if raw.empty:
                    raise RuntimeError("Aucune donnée reçue.")

                close = raw["Close"]

                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]

                close = close.rename(ticker)
                downloaded_series.append(close)

                print(f"{ticker} : téléchargement réussi")
                success = True
                break

            except Exception as error:
                print(
                    f"{ticker} : tentative {attempt}/{max_retries} échouée "
                    f"({error})"
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)

        if not success:
            failed_tickers.append(ticker)

        time.sleep(5)

    if downloaded_series:
        downloaded_prices = pd.concat(downloaded_series, axis=1)

        if cached_prices.empty:
            prices = downloaded_prices
        else:
            prices = cached_prices.join(
                downloaded_prices,
                how="outer",
            )
    else:
        prices = cached_prices

    if prices.empty:
        raise RuntimeError(
            "Aucune donnée de prix disponible."
        )

    prices.index.name = "date"

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(CACHE_PATH)

    if failed_tickers:
        print(f"Tickers non téléchargés : {failed_tickers}")

    available_tickers = [
        ticker for ticker in tickers
        if ticker in prices.columns
    ]

    return prices[available_tickers].dropna(how="all")