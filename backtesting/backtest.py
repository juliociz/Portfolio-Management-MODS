# backtesting/backtest.py
"""
Module de backtesting.
Compare la stratégie sentiment+momentum vs une stratégie passive (buy & hold S&P500).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import TICKERS, START_DATE, END_DATE, REBALANCE_FREQ, INITIAL_CAPITAL, BENCHMARK_TICKER


def run_backtest(
    prices: pd.DataFrame,
    weights_history: dict,
    initial_capital: float = INITIAL_CAPITAL,
) -> pd.DataFrame:
    """
    Simule le portefeuille avec rééquilibrage périodique.

    Args:
        prices          : DataFrame des prix (index=date, colonnes=tickers)
        weights_history : dict { date_str: {ticker: poids} }
                          Les poids sont appliqués à chaque date de rééquilibrage.
        initial_capital : Capital initial en USD

    Returns:
        DataFrame avec colonnes [portfolio_value, daily_return] par date
    """
    portfolio_value = initial_capital
    portfolio       = pd.Series(dtype=float)  # {ticker: nb_actions}
    results         = []

    dates           = prices.index
    rebalance_dates = set(
        prices.resample(REBALANCE_FREQ).last().index.strftime("%Y-%m-%d")
    )

    for date in dates:
        date_str = date.strftime("%Y-%m-%d")

        # Rééquilibrage si date de rebalancement ET poids disponibles
        if date_str in rebalance_dates and date_str in weights_history:
            weights = weights_history[date_str]
            day_prices = prices.loc[date]

            # Calcul du nombre d'actions par ticker
            portfolio = pd.Series({
                ticker: (portfolio_value * w) / day_prices[ticker]
                for ticker, w in weights.items()
                if ticker in day_prices and day_prices[ticker] > 0
            })

        # Valorisation du portefeuille
        if not portfolio.empty:
            day_prices    = prices.loc[date, portfolio.index]
            portfolio_value = (portfolio * day_prices).sum()

        results.append({"date": date, "portfolio_value": portfolio_value})

    df = pd.DataFrame(results).set_index("date")
    df["daily_return"] = df["portfolio_value"].pct_change()
    return df


def compute_metrics(portfolio_df: pd.DataFrame) -> dict:
    """
    Calcule les métriques de performance du portefeuille.

    Returns:
        dict avec total_return, annualized_return, volatility, sharpe_ratio, max_drawdown
    """
    returns = portfolio_df["daily_return"].dropna()
    values  = portfolio_df["portfolio_value"]

    total_return      = (values.iloc[-1] / values.iloc[0]) - 1
    annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility        = returns.std() * np.sqrt(252)
    sharpe_ratio      = annualized_return / volatility if volatility > 0 else 0

    # Max drawdown
    rolling_max = values.cummax()
    drawdown    = (values - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    return {
        "total_return":      round(total_return * 100, 2),
        "annualized_return": round(annualized_return * 100, 2),
        "volatility":        round(volatility * 100, 2),
        "sharpe_ratio":      round(sharpe_ratio, 3),
        "max_drawdown":      round(max_drawdown * 100, 2),
    }


def plot_performance(
    portfolio_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    save_path: str = "data/processed/backtest_results.png",
):
    """
    Trace la performance du portefeuille vs le benchmark (S&P 500).
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # Normalisation à 100 au départ
    port_norm  = portfolio_df["portfolio_value"] / portfolio_df["portfolio_value"].iloc[0] * 100
    bench_norm = benchmark_df["portfolio_value"] / benchmark_df["portfolio_value"].iloc[0] * 100

    # Graphe 1 : Évolution de la valeur
    axes[0].plot(port_norm,  label="Stratégie Sentiment+Momentum", color="steelblue", linewidth=2)
    axes[0].plot(bench_norm, label="S&P 500 (benchmark)",          color="gray",      linewidth=1.5, linestyle="--")
    axes[0].set_title("Performance du portefeuille vs S&P 500", fontsize=14)
    axes[0].set_ylabel("Valeur (base 100)")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Graphe 2 : Drawdown
    rolling_max = port_norm.cummax()
    drawdown    = (port_norm - rolling_max) / rolling_max * 100
    axes[1].fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.4, label="Drawdown")
    axes[1].set_title("Drawdown (%)", fontsize=14)
    axes[1].set_ylabel("Drawdown (%)")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"[backtest] Graphique sauvegardé : {save_path}")
    plt.show()


def print_report(strategy_metrics: dict, benchmark_metrics: dict):
    """Affiche un tableau comparatif des performances."""
    print("\n" + "=" * 55)
    print(f"{'Métrique':<25} {'Stratégie':>12} {'S&P 500':>12}")
    print("=" * 55)
    for key in strategy_metrics:
        label = key.replace("_", " ").capitalize()
        s_val = strategy_metrics[key]
        b_val = benchmark_metrics.get(key, "-")
        unit  = "%" if "return" in key or "volatility" in key or "drawdown" in key else ""
        print(f"{label:<25} {str(s_val) + unit:>12} {str(b_val) + unit:>12}")
    print("=" * 55 + "\n")
