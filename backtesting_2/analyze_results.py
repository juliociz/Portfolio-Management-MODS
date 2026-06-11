"""
analyze_results.py

Analyse les résultats du backtest, compare les stratégies et génère
backtest_chart.png.

Usage :
    python -m backtesting_2.analyze_results
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd

from backtesting_2.config_backtest import (
    TICKERS,
    INITIAL_CAPITAL,
    PORTFOLIO_RET_CSV,
    WEIGHTS_HIST_CSV,
    SUMMARY_JSON,
    BACKTEST_CHART_PNG,
    RESULTS_DIR,
    BACKTEST_START,
    BACKTEST_END,
)

logger = logging.getLogger(__name__)


def compute_metrics(portfolio_returns: pd.Series, label: str = "") -> dict:
    rets = portfolio_returns.values
    n = len(rets)

    total = float((1 + portfolio_returns).prod() - 1)
    ann_ret = float((1 + total) ** (252 / n) - 1) if n > 0 else 0.0
    ann_vol = float(np.std(rets, ddof=1) * np.sqrt(252)) if n > 1 else 0.0
    sharpe = (ann_ret - 0.02) / ann_vol if ann_vol > 1e-10 else 0.0

    cum = (1 + portfolio_returns).cumprod()
    peak = cum.cummax()
    dd = (cum - peak) / peak
    max_dd = float(dd.min()) if len(dd) else 0.0

    return {
        "strategie": label,
        "rendement_total": round(total, 4),
        "rendement_annualise": round(ann_ret, 4),
        "volatilite_annualisee": round(ann_vol, 4),
        "sharpe_ratio": round(float(sharpe), 4),
        "max_drawdown": round(max_dd, 4),
        "n_jours": n,
    }


def benchmark_equal_weight(prices: pd.DataFrame, start: str, end: str) -> pd.Series:
    subset = prices.loc[start:end].reindex(columns=TICKERS)
    daily_rets = subset.pct_change().dropna()
    eq_rets = daily_rets.mean(axis=1)
    eq_rets.name = "equal_weight"
    return eq_rets


def benchmark_pypfopt_classic(prices: pd.DataFrame, start: str, end: str) -> pd.Series:
    """
    PyPortfolioOpt classique sans signal :
      mu historique + Ledoit-Wolf + max_sharpe.
    """
    from pypfopt.expected_returns import mean_historical_return
    from pypfopt.risk_models import CovarianceShrinkage
    from pypfopt.efficient_frontier import EfficientFrontier
    from backtesting_2.config_backtest import WEIGHT_BOUNDS, RISK_FREE_RATE, FREQUENCY

    train = prices.loc[:start].reindex(columns=TICKERS).ffill().dropna(how="all")

    if len(train) < 30:
        weights = {ticker: 1 / len(TICKERS) for ticker in TICKERS}
    else:
        mu = mean_historical_return(train, frequency=FREQUENCY)
        S = CovarianceShrinkage(train, frequency=FREQUENCY).ledoit_wolf()

        try:
            ef = EfficientFrontier(mu, S, weight_bounds=WEIGHT_BOUNDS)
            ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
            weights = dict(ef.clean_weights())
        except Exception:
            try:
                ef = EfficientFrontier(mu, S, weight_bounds=WEIGHT_BOUNDS)
                ef.min_volatility()
                weights = dict(ef.clean_weights())
            except Exception:
                weights = {ticker: 1 / len(TICKERS) for ticker in TICKERS}

    test_prices = prices.loc[start:end].reindex(columns=TICKERS)
    daily_rets = test_prices.pct_change().dropna()
    pf_rets = sum(float(weights.get(ticker, 0.0)) * daily_rets[ticker] for ticker in TICKERS)
    pf_rets.name = "pypfopt_classic"
    return pf_rets


def plot_results(
    signal_rets: pd.Series,
    eq_rets: pd.Series | None = None,
    classic_rets: pd.Series | None = None,
    weights_df: pd.DataFrame | None = None,
) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, axes = plt.subplots(2, 1, figsize=(12, 9))
    fig.suptitle(
        "Backtest PyPortfolioOpt — FinBERT + Momentum",
        fontsize=13,
        fontweight="bold",
    )

    ax1 = axes[0]
    cum_signal = (1 + signal_rets).cumprod() * INITIAL_CAPITAL
    ax1.plot(cum_signal.index, cum_signal.values, label="Signal-adjusted PyPortfolioOpt", linewidth=2)

    if eq_rets is not None and not eq_rets.empty:
        eq_aligned = eq_rets.reindex(signal_rets.index).fillna(0)
        cum_eq = (1 + eq_aligned).cumprod() * INITIAL_CAPITAL
        ax1.plot(cum_eq.index, cum_eq.values, label="Equal-weight", linestyle="--")

    if classic_rets is not None and not classic_rets.empty:
        classic_aligned = classic_rets.reindex(signal_rets.index).fillna(0)
        cum_cl = (1 + classic_aligned).cumprod() * INITIAL_CAPITAL
        ax1.plot(cum_cl.index, cum_cl.values, label="PyPortfolioOpt classique", linestyle=":")

    ax1.axhline(INITIAL_CAPITAL, linewidth=0.8, linestyle="-")
    ax1.set_ylabel("Valeur du portefeuille ($)")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    if weights_df is not None and not weights_df.empty:
        weights_pivot = weights_df.pivot(index="date", columns="ticker", values="weight").fillna(0.0)
        weights_pivot.index = pd.to_datetime(weights_pivot.index)

        bottom = np.zeros(len(weights_pivot))
        for ticker in TICKERS:
            if ticker in weights_pivot.columns:
                ax2.bar(
                    weights_pivot.index,
                    weights_pivot[ticker].values,
                    bottom=bottom,
                    label=ticker,
                    width=0.8,
                )
                bottom = bottom + weights_pivot[ticker].values

        ax2.set_ylabel("Poids du portefeuille")
        ax2.set_ylim(0, 1.05)
        ax2.legend(loc="upper right", fontsize=9, ncol=5)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax2.grid(True, alpha=0.3, axis="y")
    else:
        ax2.text(0.5, 0.5, "Données de poids indisponibles", ha="center", va="center")

    plt.tight_layout()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(BACKTEST_CHART_PNG, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info("Graphique sauvegardé : %s", BACKTEST_CHART_PNG)


def analyze() -> None:
    if not PORTFOLIO_RET_CSV.exists():
        logger.error("Fichier introuvable : %s. Lance d'abord engine_pypfopt.", PORTFOLIO_RET_CSV)
        return

    returns_df = pd.read_csv(PORTFOLIO_RET_CSV, parse_dates=["date"])
    returns_df = returns_df.set_index("date").sort_index()
    signal_rets = returns_df["portfolio_return"]

    weights_df = pd.read_csv(WEIGHTS_HIST_CSV) if WEIGHTS_HIST_CSV.exists() else pd.DataFrame()

    metrics_signal = compute_metrics(signal_rets, "Signal-adjusted PyPortfolioOpt")

    print("\n" + "=" * 60)
    print("ANALYSE DU BACKTEST")
    print("=" * 60)
    for key, value in metrics_signal.items():
        print(f"  {key:<35} {value}")

    try:
        from backtesting_2.prices_backtest import load_prices

        prices = load_prices()
        eq_rets = benchmark_equal_weight(prices, BACKTEST_START, BACKTEST_END)
        classic_rets = benchmark_pypfopt_classic(prices, BACKTEST_START, BACKTEST_END)

        metrics_eq = compute_metrics(eq_rets.reindex(signal_rets.index).fillna(0), "Equal-weight")
        metrics_classic = compute_metrics(classic_rets.reindex(signal_rets.index).fillna(0), "PyPortfolioOpt classique")

        comparison = pd.DataFrame([metrics_signal, metrics_eq, metrics_classic])
        print("\n" + comparison.to_string(index=False))

        plot_results(signal_rets, eq_rets, classic_rets, weights_df)

    except Exception as exc:
        logger.warning("Benchmarks indisponibles (%s). Graphique signal seul.", exc)
        plot_results(signal_rets, weights_df=weights_df)

    if SUMMARY_JSON.exists():
        with open(SUMMARY_JSON, encoding="utf-8") as f:
            summary = json.load(f)
        summary.update({key: value for key, value in metrics_signal.items() if key != "strategie"})
        with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\nsummary.json mis à jour → {SUMMARY_JSON}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    analyze()
