# src/data/fetch_prices.py
"""
Module de récupération des prix historiques via Yahoo Finance.
Responsable : [camarade à assigner]
"""

import yfinance as yf
import pandas as pd
import os
from config import TICKERS, START_DATE, END_DATE, DATA_RAW_PATH


def fetch_prices(
    tickers: list = TICKERS,
    start: str = START_DATE,
    end: str = END_DATE,
    save: bool = True,
) -> pd.DataFrame:
    """
    Télécharge les prix de clôture ajustés pour une liste de tickers.

    Returns:
        DataFrame avec les prix de clôture, index = date, colonnes = tickers
    """
    print(f"[fetch_prices] Téléchargement de {tickers} du {start} au {end}...")

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True)
    prices = raw["Close"]

    # Supprimer les jours sans données (week-end, fériés)
    prices = prices.dropna(how="all")

    if save:
        os.makedirs(DATA_RAW_PATH, exist_ok=True)
        path = os.path.join(DATA_RAW_PATH, "prices.csv")
        prices.to_csv(path)
        print(f"[fetch_prices] Sauvegardé dans {path}")

    return prices


def load_prices() -> pd.DataFrame:
    """Charge les prix depuis le fichier CSV local."""
    path = os.path.join(DATA_RAW_PATH, "prices.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}. Lance fetch_prices() d'abord.")
    return pd.read_csv(path, index_col=0, parse_dates=True)


if __name__ == "__main__":
    df = fetch_prices()
    print(df.tail())
    print(f"Shape : {df.shape}")
