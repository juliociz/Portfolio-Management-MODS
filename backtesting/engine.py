"""
Moteur de backtesting V1 sur mai 2026.

Usage depuis la racine du projet :
    python -m backtesting.engine

Le dossier backtesting/data_input doit contenir des fichiers :
    alphavantage_merged_20260501.json
    alphavantage_merged_20260504.json
    ...

Convention : chaque fichier contient les articles disponibles pour prendre la décision du jour.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backtesting.allocator_backtest import (
    PortfolioState,
    allocate_initial,
    rebalance_portfolio,
    weights_from_scores,
)
from backtesting.config_backtest import (
    ARTICLE_FILE_PREFIX,
    BACKTEST_END,
    BACKTEST_START,
    DATA_INPUT_DIR,
    DATA_OUTPUT_DIR,
    INITIAL_CAPITAL,
    RESULTS_DIR,
    TICKERS,
)
from backtesting.prices_backtest import get_latest_prices, load_backtest_prices
from backtesting.signal_backtest import compute_daily_signal


def discover_signal_days(data_input_dir: Path = DATA_INPUT_DIR) -> list[str]:
    """Déduit les dates YYYY-MM-DD depuis les fichiers alphavantage_merged_YYYYMMDD.json."""
    files = sorted(data_input_dir.glob(f"{ARTICLE_FILE_PREFIX}*.json"))
    days: list[str] = []
    for path in files:
        raw = path.stem.replace(ARTICLE_FILE_PREFIX, "")
        if len(raw) != 8 or not raw.isdigit():
            print(f"[WARN] Fichier ignoré, nom non conforme : {path.name}")
            continue
        day = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        if BACKTEST_START <= day <= BACKTEST_END:
            days.append(day)
    return sorted(days)


def _compute_max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    max_dd = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = (peak - value) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, drawdown)
    return max_dd


def run_backtest() -> None:
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    days = discover_signal_days(DATA_INPUT_DIR)
    if not days:
        raise RuntimeError(
            f"Aucun fichier {ARTICLE_FILE_PREFIX}YYYYMMDD.json trouvé dans {DATA_INPUT_DIR}."
        )

    print("=" * 70)
    print("BACKTEST V1 — Sentiment + Momentum — Mai 2026")
    print(f"Jours trouvés : {len(days)} | {days[0]} → {days[-1]}")
    print(f"Capital initial : {INITIAL_CAPITAL:,.2f} $")
    print(f"Tickers : {TICKERS}")
    print("=" * 70)

    prices = load_backtest_prices(start=days[0], end=days[-1])

    portfolio: PortfolioState | None = None
    history_rows: list[dict] = []
    transactions_rows: list[dict] = []
    all_sentiment: list[pd.DataFrame] = []
    all_momentum: list[pd.DataFrame] = []
    all_scores: list[pd.DataFrame] = []

    for index, day in enumerate(days, start=1):
        compact_day = day.replace("-", "")
        json_path = DATA_INPUT_DIR / f"{ARTICLE_FILE_PREFIX}{compact_day}.json"

        # On ignore les dates où il n'y a pas de clôture disponible avant ou à J.
        try:
            latest_prices = get_latest_prices(prices, day)
        except ValueError as exc:
            print(f"[SKIP] {day} : {exc}")
            continue

        print("\n" + "-" * 70)
        print(f"Jour {index}/{len(days)} — {day}")
        print("-" * 70)

        sentiment_df, momentum_df, scores_df = compute_daily_signal(
            json_path=str(json_path),
            prices=prices,
            day=day,
        )
        target_weights = weights_from_scores(scores_df)

        if portfolio is None:
            portfolio, transactions = allocate_initial(
                capital=INITIAL_CAPITAL,
                target_weights=target_weights,
                prices=latest_prices,
                day=day,
            )
        else:
            portfolio, transactions = rebalance_portfolio(
                previous=portfolio,
                target_weights=target_weights,
                prices=latest_prices,
                day=day,
            )

        total_value = portfolio.total_value(latest_prices)
        realized_weights = portfolio.weights(latest_prices)
        pnl = total_value - INITIAL_CAPITAL

        print(f"Valeur portefeuille : {total_value:,.2f} $ | P&L : {pnl:+,.2f} $")
        print(f"Cash : {portfolio.cash:,.2f} $")
        print("Holdings :", portfolio.holdings)
        print(f"Transactions : {len(transactions)}")

        history_row = {
            "date": day,
            "total_value": round(total_value, 2),
            "cash": round(portfolio.cash, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl / INITIAL_CAPITAL * 100, 4),
        }
        for ticker in TICKERS:
            history_row[f"shares_{ticker}"] = int(portfolio.holdings.get(ticker, 0))
            history_row[f"price_{ticker}"] = round(float(latest_prices[ticker]), 4)
            history_row[f"target_weight_{ticker}"] = round(float(target_weights.get(ticker, 0.0)), 6)
            history_row[f"realized_weight_{ticker}"] = round(float(realized_weights.get(ticker, 0.0)), 6)

        history_rows.append(history_row)
        transactions_rows.extend(transactions)
        all_sentiment.append(sentiment_df)
        all_momentum.append(momentum_df)
        all_scores.append(scores_df)

    history = pd.DataFrame(history_rows)
    transactions = pd.DataFrame(transactions_rows)
    daily_sentiment = pd.concat(all_sentiment, ignore_index=True) if all_sentiment else pd.DataFrame()
    daily_momentum = pd.concat(all_momentum, ignore_index=True) if all_momentum else pd.DataFrame()
    daily_scores = pd.concat(all_scores, ignore_index=True) if all_scores else pd.DataFrame()

    history.to_csv(RESULTS_DIR / "portfolio_history.csv", index=False)
    transactions.to_csv(RESULTS_DIR / "transactions_log.csv", index=False)
    daily_sentiment.to_csv(DATA_OUTPUT_DIR / "daily_sentiment_scores.csv", index=False)
    daily_momentum.to_csv(DATA_OUTPUT_DIR / "daily_momentum_scores.csv", index=False)
    daily_scores.to_csv(DATA_OUTPUT_DIR / "daily_target_weights.csv", index=False)

    if history.empty:
        raise RuntimeError("Backtest terminé sans aucune journée exploitable.")

    final_value = float(history["total_value"].iloc[-1])
    max_drawdown = _compute_max_drawdown(history["total_value"].tolist())
    summary = {
        "capital_initial": INITIAL_CAPITAL,
        "valeur_finale": round(final_value, 2),
        "pnl_absolu": round(final_value - INITIAL_CAPITAL, 2),
        "pnl_pct": round((final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100, 4),
        "max_drawdown_pct": round(max_drawdown * 100, 4),
        "nb_jours": int(len(history)),
        "nb_transactions": int(len(transactions)),
        "periode": {"start": history["date"].iloc[0], "end": history["date"].iloc[-1]},
    }

    with open(RESULTS_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("RÉSULTATS FINAUX")
    print("=" * 70)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nFichiers générés :")
    print(f"- {RESULTS_DIR / 'portfolio_history.csv'}")
    print(f"- {RESULTS_DIR / 'transactions_log.csv'}")
    print(f"- {RESULTS_DIR / 'summary.json'}")
    print(f"- {DATA_OUTPUT_DIR / 'daily_sentiment_scores.csv'}")
    print(f"- {DATA_OUTPUT_DIR / 'daily_momentum_scores.csv'}")
    print(f"- {DATA_OUTPUT_DIR / 'daily_target_weights.csv'}")


if __name__ == "__main__":
    run_backtest()
