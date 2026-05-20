# main.py
"""
Point d'entrée du pipeline Portfolio-Management-MODS.

Usage :
    python main.py --version v1          # Sentiment + Momentum
    python main.py --version v2          # + Black-Litterman
    python main.py --fetch-only          # Juste télécharger les données
"""

import argparse
import os
import pandas as pd

from src.data.fetch_prices   import fetch_prices, load_prices
from src.data.fetch_news     import fetch_news, load_news
from src.sentiment.finbert   import compute_ticker_sentiment
from src.momentum.momentum   import compute_momentum
from src.portfolio.scorer    import compute_global_score
from src.portfolio.optimizer import optimize_max_sharpe, optimize_black_litterman, discrete_allocation
from config import TICKERS, START_DATE, END_DATE, INITIAL_CAPITAL, DATA_PROCESSED_PATH


def parse_args():
    parser = argparse.ArgumentParser(description="Portfolio Management - Sentiment + Momentum")
    parser.add_argument("--version",    choices=["v1", "v2"], default="v1")
    parser.add_argument("--fetch-only", action="store_true", help="Télécharger les données uniquement")
    parser.add_argument("--no-fetch",   action="store_true", help="Utiliser les données locales existantes")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(DATA_PROCESSED_PATH, exist_ok=True)

    # ========================
    # ÉTAPE 1 : Données
    # ========================
    print("\n📥 Étape 1 : Récupération des données")
    print("-" * 40)

    if args.no_fetch:
        print("Chargement des données locales...")
        prices   = load_prices()
        articles = load_news()
    else:
        prices   = fetch_prices(tickers=TICKERS, start=START_DATE, end=END_DATE)
        articles = fetch_news(tickers=TICKERS)

    if args.fetch_only:
        print("\n✅ Données téléchargées. Arrêt (--fetch-only).")
        return

    # ========================
    # ÉTAPE 2 : Sentiment
    # ========================
    print("\n🧠 Étape 2 : Analyse de sentiment (FinBERT)")
    print("-" * 40)
    sentiment_df = compute_ticker_sentiment(articles)
    print(sentiment_df.to_string(index=False))

    sentiment_path = os.path.join(DATA_PROCESSED_PATH, "sentiment_scores.csv")
    sentiment_df.to_csv(sentiment_path, index=False)

    # ========================
    # ÉTAPE 3 : Momentum
    # ========================
    print("\n📈 Étape 3 : Calcul du momentum")
    print("-" * 40)
    momentum_df = compute_momentum(prices)
    print(momentum_df.to_string(index=False))

    momentum_path = os.path.join(DATA_PROCESSED_PATH, "momentum_scores.csv")
    momentum_df.to_csv(momentum_path, index=False)

    # ========================
    # ÉTAPE 4 : Score global
    # ========================
    print("\n⚖️  Étape 4 : Score global (sentiment + momentum)")
    print("-" * 40)
    scores_df = compute_global_score(sentiment_df, momentum_df)
    print(scores_df.to_string(index=False))

    scores_path = os.path.join(DATA_PROCESSED_PATH, "global_scores.csv")
    scores_df.to_csv(scores_path, index=False)

    # ========================
    # ÉTAPE 5 : Optimisation
    # ========================
    print(f"\n🏗️  Étape 5 : Optimisation du portefeuille ({args.version.upper()})")
    print("-" * 40)

    if args.version == "v1":
        result = optimize_max_sharpe(prices)
    else:
        result = optimize_black_litterman(prices, scores_df)

    weights = result["weights"]
    perf    = result["performance"]

    print("\nPoids optimaux :")
    for ticker, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {ticker}: {w*100:.1f}%")

    print(f"\nPerformance attendue :")
    print(f"  Rendement annuel : {perf['expected_return']*100:.2f}%")
    print(f"  Volatilité       : {perf['volatility']*100:.2f}%")
    print(f"  Ratio de Sharpe  : {perf['sharpe_ratio']:.3f}")

    # Allocation discrète
    print(f"\n💰 Allocation pour {INITIAL_CAPITAL:,.0f} USD :")
    allocation, leftover = discrete_allocation(weights, prices)
    for ticker, nb in sorted(allocation.items()):
        print(f"  {ticker}: {nb} actions")
    print(f"  Cash restant : ${leftover:,.2f}")

    print("\n✅ Pipeline terminé.")


if __name__ == "__main__":
    main()
