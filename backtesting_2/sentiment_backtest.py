"""
sentiment_backtest.py

Charge un fichier alphavantage_merged_YYYYMMDD.json et calcule
les scores de sentiment FinBERT pour chaque ticker.

Format attendu du JSON :
{
    "TSLA": ["texte article 1", "texte article 2", ...],
    "NKE":  ["texte article 1", ...],
    ...
}

Ce module est autonome : il ne dépend pas de Traitement/sentiment/finbert.py.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from backtesting_2.config_backtest import TICKERS, DATA_INPUT

logger = logging.getLogger(__name__)

# ── Chargement FinBERT lazy ───────────────────────────────────────────────────
_pipeline = None


def _load_finbert():
    """Charge FinBERT une seule fois, au premier appel."""
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline

            logger.info("Chargement du modèle FinBERT ProsusAI/finbert...")
            _pipeline = hf_pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                top_k=None,
            )
            logger.info("FinBERT chargé.")
        except Exception as exc:
            logger.warning(
                "Impossible de charger FinBERT (%s). "
                "Fallback : scores de sentiment neutres.",
                exc,
            )
            _pipeline = None
    return _pipeline


def _score_article(text: str, pipe) -> float:
    """Retourne P(positive) - P(negative) pour un article."""
    if not text:
        return 0.0

    try:
        # Le pipeline gère la troncature au niveau tokenizer.
        results = pipe(text, truncation=True, max_length=512)[0]
        proba = {r["label"].lower(): float(r["score"]) for r in results}
        return proba.get("positive", 0.0) - proba.get("negative", 0.0)
    except Exception as exc:
        logger.debug("Erreur scoring article : %s", exc)
        return 0.0


def compute_daily_sentiment(articles_file: Path) -> pd.DataFrame:
    """
    Lit un fichier alphavantage_merged_YYYYMMDD.json et retourne :
        ticker | sentiment_score | n_articles

    Si le fichier est absent ou si un ticker n'a pas d'articles,
    le score est 0.0.
    """
    articles_by_ticker: dict[str, list[str]] = {}

    if articles_file.exists():
        try:
            with open(articles_file, encoding="utf-8") as f:
                raw = json.load(f)
            articles_by_ticker = {ticker: raw.get(ticker, []) for ticker in TICKERS}
        except Exception as exc:
            logger.warning("Lecture impossible de %s : %s", articles_file, exc)
    else:
        logger.warning("Fichier absent : %s. Scores neutres utilisés.", articles_file)

    pipe = _load_finbert()

    rows = []
    for ticker in TICKERS:
        texts = articles_by_ticker.get(ticker, [])
        if not texts or pipe is None:
            rows.append(
                {
                    "ticker": ticker,
                    "sentiment_score": 0.0,
                    "n_articles": len(texts),
                }
            )
            continue

        scores = [_score_article(text, pipe) for text in texts]
        sentiment_score = sum(scores) / len(scores) if scores else 0.0

        rows.append(
            {
                "ticker": ticker,
                "sentiment_score": round(sentiment_score, 6),
                "n_articles": len(texts),
            }
        )

    return pd.DataFrame(rows)


def articles_file_for_date(date: pd.Timestamp) -> Path:
    """Retourne le chemin du fichier JSON pour une date donnée."""
    return DATA_INPUT / f"alphavantage_merged_{date.strftime('%Y%m%d')}.json"


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    parser = argparse.ArgumentParser(description="Test sentiment FinBERT sur un fichier JSON.")
    parser.add_argument("json_file", type=str, help="Chemin vers alphavantage_merged_YYYYMMDD.json")
    args = parser.parse_args()

    df = compute_daily_sentiment(Path(args.json_file))
    print(df.to_string(index=False))
