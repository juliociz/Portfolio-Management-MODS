"""
Téléchargement des prix journaliers via Alpha Vantage.
"""

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from config import END_DATE, START_DATE, TICKERS


load_dotenv()

API_URL = "https://www.alphavantage.co/query"
CACHE_PATH = Path("data_output/prices_alphavantage.csv")


def load_prices_alphavantage(
    tickers: list[str] = TICKERS,
    start: str = START_DATE,
    end: str = END_DATE,
) -> pd.DataFrame:
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "La variable ALPHAVANTAGE_API_KEY est absente du fichier .env."
        )

    series = []

    for ticker in tickers:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "compact",
            "apikey": api_key,
        }

        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        if "Note" in payload:
            raise RuntimeError(
                f"Limite Alpha Vantage atteinte : {payload['Note']}"
            )

        if "Information" in payload:
            raise RuntimeError(
                f"Réponse Alpha Vantage : {payload['Information']}"
            )

        if "Error Message" in payload:
            raise RuntimeError(
                f"Ticker invalide {ticker} : {payload['Error Message']}"
            )

        time_series = payload.get("Time Series (Daily)")

        if not time_series:
            raise RuntimeError(
                f"Aucune série journalière reçue pour {ticker}."
            )

        close = pd.Series(
            {
                pd.to_datetime(date): float(values["4. close"])
                for date, values in time_series.items()
            },
            name=ticker,
        ).sort_index()

        close = close.loc[:end]
        series.append(close)

        print(f"{ticker} : téléchargement réussi")

        # Évite d'enchaîner trop rapidement les appels.
        time.sleep(15)

    prices = pd.concat(series, axis=1)
    prices.index.name = "date"

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(CACHE_PATH)

    return prices.dropna(how="all")


if __name__ == "__main__":
    prices = load_prices_alphavantage()
    print(prices.tail())