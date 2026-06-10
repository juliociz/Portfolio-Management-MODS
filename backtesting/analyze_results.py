"""
Analyse simple des résultats du backtest.

Usage depuis la racine du projet :
    python -m backtesting.analyze_results
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from backtesting.config_backtest import RESULTS_DIR, TICKERS


def analyze_results(results_dir: Path = RESULTS_DIR) -> None:
    history_path = results_dir / "portfolio_history.csv"
    transactions_path = results_dir / "transactions_log.csv"
    summary_path = results_dir / "summary.json"

    if not history_path.exists():
        raise FileNotFoundError(f"Introuvable : {history_path}. Lance d'abord python -m backtesting.engine")

    history = pd.read_csv(history_path, parse_dates=["date"])
    transactions = pd.read_csv(transactions_path) if transactions_path.exists() else pd.DataFrame()

    summary = {}
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    print("=" * 60)
    print("STATISTIQUES BACKTEST")
    print("=" * 60)
    if summary:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(history[["date", "total_value", "pnl", "pnl_pct"]].tail())

    if not transactions.empty:
        print("\nTransactions par ticker :")
        print(transactions.groupby(["ticker", "action"])["shares"].sum())

    # Graphique valeur portefeuille.
    plt.figure(figsize=(10, 5))
    plt.plot(history["date"], history["total_value"], marker="o")
    plt.axhline(history["total_value"].iloc[0], linestyle="--")
    plt.title("Backtest V1 — Valeur du portefeuille")
    plt.xlabel("Date")
    plt.ylabel("Valeur ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    chart_path = results_dir / "portfolio_value.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()

    # Graphique poids réalisés.
    plt.figure(figsize=(10, 5))
    for ticker in TICKERS:
        col = f"realized_weight_{ticker}"
        if col in history.columns:
            plt.plot(history["date"], history[col] * 100, marker="o", label=ticker)
    plt.title("Backtest V1 — Poids réalisés")
    plt.xlabel("Date")
    plt.ylabel("Poids (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    weights_chart_path = results_dir / "realized_weights.png"
    plt.savefig(weights_chart_path, dpi=150)
    plt.close()

    print("\nGraphiques générés :")
    print(f"- {chart_path}")
    print(f"- {weights_chart_path}")


if __name__ == "__main__":
    analyze_results()
