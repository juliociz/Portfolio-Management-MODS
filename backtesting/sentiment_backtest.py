"""
Calcul du sentiment journalier pour le backtest.

Ce module réutilise la fonction FinBERT existante :
    Traitement.sentiment.finbert.compute_ticker_sentiment

Format attendu du JSON journalier :
{
    "TSLA": ["texte article 1", "texte article 2", ...],
    "NKE":  ["texte article 1", ...],
    ...
}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from Traitement.sentiment.finbert import compute_ticker_sentiment
from backtesting.config_backtest import TICKERS


def load_articles_json(json_path: str | Path) -> dict[str, list[str]]:
    """Charge un fichier alphavantage_merged_YYYYMMDD.json."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Le JSON doit être un dictionnaire {ticker: [textes]}.")

    # Garantit que tous les tickers existent, même si score neutre faute d'articles.
    normalized: dict[str, list[str]] = {}
    for ticker in TICKERS:
        texts = data.get(ticker, [])
        if texts is None:
            texts = []
        if not isinstance(texts, list):
            raise ValueError(f"La valeur associée à {ticker} doit être une liste de textes.")
        normalized[ticker] = texts

    return normalized


def compute_daily_sentiment(json_path: str | Path, day: str | None = None) -> pd.DataFrame:
    """
    Calcule le sentiment FinBERT pour un fichier journalier.

    Returns:
        DataFrame avec colonnes : date | ticker | sentiment_score | n_articles
    """
    articles = load_articles_json(json_path)
    df = compute_ticker_sentiment(articles)
    if day is not None:
        df.insert(0, "date", day)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Calcul sentiment FinBERT pour un fichier journalier")
    parser.add_argument("json_path", type=str, help="Chemin vers alphavantage_merged_YYYYMMDD.json")
    parser.add_argument("--date", type=str, default=None, help="Date YYYY-MM-DD à ajouter au DataFrame")
    args = parser.parse_args()

    df = compute_daily_sentiment(args.json_path, day=args.date)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
