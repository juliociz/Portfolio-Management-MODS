"""
engine_pypfopt.py

Boucle principale du backtest.

Pour chaque jour J de mai 2026 :
  1. charge le fichier alphavantage_merged_YYYYMMDD.json ;
  2. calcule le sentiment FinBERT ;
  3. calcule le momentum ;
  4. construit le global_score ;
  5. transforme les signaux en mu/S pour PyPortfolioOpt ;
  6. optimise des poids continus ;
  7. mesure la performance out-of-sample J → J+1.

Lancement :
    python -m backtesting_2.engine_pypfopt

Option risque ajusté :
    python -m backtesting_2.engine_pypfopt --adjust-covariance
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    BACKTEST_START,
    BACKTEST_END,
    INITIAL_CAPITAL,
    DATA_OUTPUT,
    RESULTS_DIR,
    SENTIMENT_OUT_CSV,
    MOMENTUM_OUT_CSV,
    GLOBAL_SCORES_CSV,
    WEIGHTS_CSV,
    PORTFOLIO_RET_CSV,
    WEIGHTS_HIST_CSV,
    SUMMARY_JSON,
)
from backtesting_2.prices_backtest import load_prices, get_train_prices
from backtesting_2.sentiment_backtest import compute_daily_sentiment, articles_file_for_date
from backtesting_2.signals import compute_daily_momentum, compute_global_scores
from backtesting_2.risk_forecast import build_forecast_inputs
from backtesting_2.optimizer_pypfopt import optimize_with_pypfopt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _trading_days(prices: pd.DataFrame, start: str, end: str) -> list[pd.Timestamp]:
    return [d for d in prices.index if pd.Timestamp(start) <= d <= pd.Timestamp(end)]


def _next_day(prices: pd.DataFrame, day: pd.Timestamp) -> pd.Timestamp | None:
    future = prices.index[prices.index > day]
    return future[0] if len(future) > 0 else None


def run_backtest(adjust_covariance: bool = False) -> pd.DataFrame:
    """
    Exécute le backtest et retourne un DataFrame :
        date | portfolio_return | portfolio_value | cumulative_return
    """
    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Chargement des prix...")
    prices = load_prices()

    trading_days = _trading_days(prices, BACKTEST_START, BACKTEST_END)
    if len(trading_days) < 2:
        logger.error("Pas assez de jours de trading dans la plage demandée.")
        sys.exit(1)

    logger.info(
        "%s jours de trading détectés : %s → %s",
        len(trading_days),
        trading_days[0].date(),
        trading_days[-1].date(),
    )

    records_sentiment = []
    records_momentum = []
    records_global = []
    records_weights = []
    records_returns = []

    portfolio_value = INITIAL_CAPITAL

    for day in trading_days[:-1]:
        next_day = _next_day(prices, day)
        if next_day is None:
            break

        logger.info("── %s ──────────────────────", day.date())

        train_prices = get_train_prices(prices, day)

        articles_file = articles_file_for_date(day)
        sentiment_df = compute_daily_sentiment(articles_file)

        momentum_df = compute_daily_momentum(train_prices, as_of=day)
        global_df = compute_global_scores(sentiment_df, momentum_df)

        try:
            mu_adj, S = build_forecast_inputs(
                train_prices,
                global_df,
                adjust_covariance=adjust_covariance,
            )
            weights = optimize_with_pypfopt(mu_adj, S)
        except Exception as exc:
            logger.warning("Optimisation impossible (%s). Equal-weight utilisé.", exc)
            eq = 1.0 / len(TICKERS)
            weights = {ticker: eq for ticker in TICKERS}

        price_j = prices.loc[day].reindex(TICKERS)
        price_j1 = prices.loc[next_day].reindex(TICKERS)
        asset_returns = (price_j1 / price_j - 1.0).fillna(0.0)

        portfolio_return = sum(weights.get(ticker, 0.0) * float(asset_returns[ticker]) for ticker in TICKERS)
        portfolio_value = portfolio_value * (1.0 + portfolio_return)

        for _, row in sentiment_df.iterrows():
            records_sentiment.append({"date": day.date().isoformat(), **row.to_dict()})

        for _, row in momentum_df.iterrows():
            records_momentum.append({"date": day.date().isoformat(), **row.to_dict()})

        for _, row in global_df.iterrows():
            records_global.append({"date": day.date().isoformat(), **row.to_dict()})

        for ticker in TICKERS:
            records_weights.append(
                {
                    "date": day.date().isoformat(),
                    "ticker": ticker,
                    "weight": round(float(weights.get(ticker, 0.0)), 8),
                }
            )

        records_returns.append(
            {
                "date": day.date().isoformat(),
                "next_date": next_day.date().isoformat(),
                "portfolio_return": round(float(portfolio_return), 10),
                "portfolio_value": round(float(portfolio_value), 4),
            }
        )

        logger.info("Poids : %s", " | ".join(f"{t}={weights[t]:.3f}" for t in TICKERS))
        logger.info(
    f"Rendement J→J+1 : {portfolio_return * 100:+.4f}% | "
    f"Valeur : {portfolio_value:,.2f} $"
)

    pd.DataFrame(records_sentiment).to_csv(SENTIMENT_OUT_CSV, index=False)
    pd.DataFrame(records_momentum).to_csv(MOMENTUM_OUT_CSV, index=False)
    pd.DataFrame(records_global).to_csv(GLOBAL_SCORES_CSV, index=False)
    pd.DataFrame(records_weights).to_csv(WEIGHTS_CSV, index=False)

    returns_df = pd.DataFrame(records_returns)
    if returns_df.empty:
        raise RuntimeError("Aucun rendement n'a été calculé.")

    returns_df["cumulative_return"] = (1 + returns_df["portfolio_return"]).cumprod() - 1
    returns_df.to_csv(PORTFOLIO_RET_CSV, index=False)

    weights_hist_df = pd.DataFrame(records_weights)
    weights_hist_df.to_csv(WEIGHTS_HIST_CSV, index=False)

    summary = _compute_summary(returns_df)
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info("CSV sauvegardés dans %s et %s", DATA_OUTPUT, RESULTS_DIR)
    logger.info("summary.json → %s", SUMMARY_JSON)

    return returns_df


def _compute_summary(returns_df: pd.DataFrame) -> dict:
    import numpy as np

    rets = returns_df["portfolio_return"].values
    total_return = float(returns_df["cumulative_return"].iloc[-1])
    n_days = len(rets)

    ann_vol = float(np.std(rets, ddof=1) * np.sqrt(252)) if n_days > 1 else 0.0
    ann_ret = float((1 + total_return) ** (252 / n_days) - 1) if n_days > 0 else 0.0
    sharpe = (ann_ret - 0.02) / ann_vol if ann_vol > 1e-10 else 0.0

    values = returns_df["portfolio_value"].values
    peak = values[0]
    max_dd = 0.0
    for value in values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    return {
        "capital_initial": INITIAL_CAPITAL,
        "capital_final": round(float(returns_df["portfolio_value"].iloc[-1]), 2),
        "rendement_total": round(total_return, 6),
        "volatilite_annualisee": round(ann_vol, 6),
        "sharpe_ratio": round(float(sharpe), 4),
        "max_drawdown": round(float(max_dd), 6),
        "n_jours": int(n_days),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest PyPortfolioOpt FinBERT + Momentum.")
    parser.add_argument(
        "--adjust-covariance",
        action="store_true",
        help="Active l'ajustement de la covariance par les signaux négatifs.",
    )
    args = parser.parse_args()

    df = run_backtest(adjust_covariance=args.adjust_covariance)
    summary = _compute_summary(df)

    logger.info("\n%s", "=" * 50)
    logger.info("RÉSUMÉ DU BACKTEST")
    logger.info("%s", "=" * 50)
    for key, value in summary.items():
        logger.info("  %-30s %s", key, value)
    logger.info("%s", "=" * 50)
