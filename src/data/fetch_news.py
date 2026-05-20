# src/data/fetch_news.py
"""
Module de récupération des articles financiers via NewsAPI.
Responsable : [camarade à assigner]
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv
from config import TICKERS, NEWS_SOURCES, NEWS_LANGUAGE, NEWS_LOOKBACK_DAYS, DATA_RAW_PATH

load_dotenv()


def _get_client() -> NewsApiClient:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise EnvironmentError("NEWS_API_KEY manquante dans le fichier .env")
    return NewsApiClient(api_key=api_key)


# Mapping ticker → mots-clés de recherche
TICKER_KEYWORDS = {
    "AAPL": "Apple stock",
    "MSFT": "Microsoft stock",
    "JPM":  "JPMorgan stock",
    "XOM":  "ExxonMobil stock",
    "JNJ":  "Johnson Johnson stock",
}


def fetch_news(
    tickers: list = TICKERS,
    lookback_days: int = NEWS_LOOKBACK_DAYS,
    save: bool = True,
) -> dict:
    """
    Récupère les articles pour chaque ticker sur les N derniers jours.

    Returns:
        dict { "AAPL": ["article texte 1", "article texte 2", ...], ... }
    """
    client = _get_client()
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)

    articles_by_ticker = {}

    for ticker in tickers:
        keyword = TICKER_KEYWORDS.get(ticker, ticker)
        print(f"[fetch_news] Récupération des news pour {ticker} ({keyword})...")

        response = client.get_everything(
            q=keyword,
            sources=",".join(NEWS_SOURCES),
            language=NEWS_LANGUAGE,
            from_param=start_date.strftime("%Y-%m-%d"),
            to=end_date.strftime("%Y-%m-%d"),
            sort_by="relevancy",
            page_size=20,
        )

        texts = []
        for article in response.get("articles", []):
            # Concaténer titre + description pour avoir plus de contexte
            title       = article.get("title") or ""
            description = article.get("description") or ""
            content     = article.get("content") or ""
            full_text   = f"{title}. {description} {content}".strip()
            if full_text:
                texts.append(full_text)

        articles_by_ticker[ticker] = texts
        print(f"  → {len(texts)} articles récupérés")

    if save:
        os.makedirs(DATA_RAW_PATH, exist_ok=True)
        path = os.path.join(DATA_RAW_PATH, "news.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(articles_by_ticker, f, ensure_ascii=False, indent=2)
        print(f"[fetch_news] Sauvegardé dans {path}")

    return articles_by_ticker


def load_news() -> dict:
    """Charge les news depuis le fichier JSON local."""
    path = os.path.join(DATA_RAW_PATH, "news.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}. Lance fetch_news() d'abord.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    articles = fetch_news()
    for ticker, texts in articles.items():
        print(f"{ticker}: {len(texts)} articles")
