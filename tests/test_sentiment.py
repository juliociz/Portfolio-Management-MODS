# tests/test_sentiment.py
"""
Tests unitaires pour le module FinBERT.
Lance avec : pytest tests/test_sentiment.py
"""

import pytest
import pandas as pd
from src.sentiment.finbert import analyze_sentiment, compute_ticker_sentiment


def test_analyze_sentiment_keys():
    """Le résultat doit contenir les 3 clés de sentiment."""
    result = analyze_sentiment("Apple reports strong earnings growth.")
    assert set(result.keys()) == {"positive", "negative", "neutral"}


def test_analyze_sentiment_sum_to_one():
    """Les probabilités doivent sommer à ~1."""
    result = analyze_sentiment("Markets are down amid global uncertainty.")
    total = sum(result.values())
    assert abs(total - 1.0) < 0.01


def test_analyze_sentiment_positive():
    """Un texte clairement positif doit avoir un score positif dominant."""
    result = analyze_sentiment("Record profits and outstanding growth exceed all expectations.")
    assert result["positive"] > result["negative"]


def test_analyze_sentiment_negative():
    """Un texte clairement négatif doit avoir un score négatif dominant."""
    result = analyze_sentiment("Bankruptcy filed, massive losses, disaster for investors.")
    assert result["negative"] > result["positive"]


def test_compute_ticker_sentiment_structure():
    """compute_ticker_sentiment doit retourner un DataFrame avec les bonnes colonnes."""
    articles = {
        "AAPL": ["Apple had a great quarter with record sales."],
        "MSFT": ["Microsoft faces regulatory challenges in Europe."],
    }
    df = compute_ticker_sentiment(articles)
    assert isinstance(df, pd.DataFrame)
    assert "ticker" in df.columns
    assert "sentiment_score" in df.columns
    assert len(df) == 2


def test_compute_ticker_sentiment_range():
    """Le sentiment_score doit être dans [-1, +1]."""
    articles = {
        "AAPL": ["Apple is performing well above market expectations."],
        "XOM":  ["ExxonMobil faces huge environmental fines and losses."],
    }
    df = compute_ticker_sentiment(articles)
    assert df["sentiment_score"].between(-1, 1).all()


def test_empty_articles():
    """Un ticker sans articles doit retourner un score de 0."""
    articles = {"JPM": []}
    df = compute_ticker_sentiment(articles)
    assert df.loc[df["ticker"] == "JPM", "sentiment_score"].values[0] == 0.0
