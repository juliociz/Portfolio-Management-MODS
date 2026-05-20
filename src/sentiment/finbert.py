# src/sentiment/finbert.py
"""
Module d'analyse de sentiment financier avec FinBERT.
Responsable : Blaiso Blaiso

Pipeline :
    articles (dict) → analyze_sentiment() → compute_ticker_sentiment() → DataFrame
"""

import torch
import torch.nn.functional as F
import pandas as pd
from tqdm import tqdm
from transformers import BertTokenizer, BertForSequenceClassification
from config import FINBERT_MODEL, MAX_TOKENS

# ========================
# Chargement lazy du modèle (une seule fois)
# ========================
_tokenizer = None
_model     = None


def _load_model():
    """Charge FinBERT en mémoire (une seule fois, lors du premier appel)."""
    global _tokenizer, _model
    if _model is None:
        print(f"[FinBERT] Chargement du modèle {FINBERT_MODEL}...")
        _tokenizer = BertTokenizer.from_pretrained(FINBERT_MODEL)
        _model     = BertForSequenceClassification.from_pretrained(FINBERT_MODEL)
        _model.eval()
        print("[FinBERT] Modèle prêt.")


# ========================
# Analyse d'un seul texte
# ========================

def analyze_sentiment(text: str) -> dict:
    """
    Analyse le sentiment d'un texte financier avec FinBERT.

    Args:
        text: texte brut (titre + corps d'article)

    Returns:
        dict avec les probabilités : {"positive": 0.7, "negative": 0.1, "neutral": 0.2}
    """
    _load_model()

    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,       # Coupe si > MAX_TOKENS
        max_length=MAX_TOKENS,
        padding=True,
    )

    with torch.no_grad():
        outputs = _model(**inputs)

    probs  = F.softmax(outputs.logits, dim=-1).squeeze()
    labels = ["positive", "negative", "neutral"]

    return {label: round(probs[i].item(), 4) for i, label in enumerate(labels)}


# ========================
# Analyse par batch (plus rapide)
# ========================

def analyze_sentiment_batch(texts: list, batch_size: int = 8) -> list:
    """
    Analyse une liste de textes par batch pour accélérer le traitement.

    Returns:
        Liste de dicts de sentiment, dans le même ordre que texts
    """
    _load_model()
    results = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = _tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_TOKENS,
            padding=True,
        )
        with torch.no_grad():
            outputs = _model(**inputs)

        probs_batch = F.softmax(outputs.logits, dim=-1)
        labels      = ["positive", "negative", "neutral"]

        for probs in probs_batch:
            results.append({label: round(probs[i].item(), 4) for i, label in enumerate(labels)})

    return results


# ========================
# Score agrégé par ticker
# ========================

def compute_ticker_sentiment(articles: dict) -> pd.DataFrame:
    """
    Calcule un score de sentiment agrégé pour chaque ticker.

    Args:
        articles: dict { "AAPL": ["texte1", "texte2", ...], "MSFT": [...] }
                  (format de sortie de fetch_news.py)

    Returns:
        DataFrame avec colonnes : ticker | sentiment_score | n_articles
        sentiment_score ∈ [-1, +1] :  -1 = très négatif, +1 = très positif
    """
    results = []

    for ticker, texts in tqdm(articles.items(), desc="Analyse sentiment"):
        if not texts:
            print(f"[FinBERT] Aucun article pour {ticker}, score = 0.0")
            results.append({"ticker": ticker, "sentiment_score": 0.0, "n_articles": 0})
            continue

        sentiments  = analyze_sentiment_batch(texts)
        net_scores  = [s["positive"] - s["negative"] for s in sentiments]
        mean_score  = sum(net_scores) / len(net_scores)

        results.append({
            "ticker":          ticker,
            "sentiment_score": round(mean_score, 4),
            "n_articles":      len(texts),
        })

    df = pd.DataFrame(results).sort_values("sentiment_score", ascending=False).reset_index(drop=True)
    return df


# ========================
# Test rapide
# ========================

if __name__ == "__main__":
    sample_articles = {
        "AAPL": [
            "Apple reports record quarterly earnings, beating analyst expectations by a wide margin.",
            "iPhone sales disappoint analysts this quarter amid slowing consumer demand.",
        ],
        "MSFT": [
            "Microsoft Azure cloud revenue surges 30%, driven by AI adoption across enterprises.",
        ],
        "JPM": [
            "JPMorgan raises dividend as profits hit record high on strong trading revenues.",
            "JPMorgan faces regulatory scrutiny over compliance failures in overseas operations.",
        ],
    }

    df = compute_ticker_sentiment(sample_articles)
    print("\n=== Scores de sentiment ===")
    print(df.to_string(index=False))
