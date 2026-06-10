"""
Allocation et rééquilibrage pour le backtest.

V1 simplifiée :
    - actions entières ;
    - pas de frais de transaction ;
    - pas de slippage ;
    - ventes avant achats pour libérer du cash.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import floor

import pandas as pd

from backtesting.config_backtest import TICKERS, TRANSACTION_COST_RATE


@dataclass
class PortfolioState:
    cash: float
    holdings: dict[str, int] = field(default_factory=dict)

    def total_value(self, prices: pd.Series | dict[str, float]) -> float:
        return float(self.cash + sum(self.holdings.get(t, 0) * float(prices[t]) for t in TICKERS))

    def weights(self, prices: pd.Series | dict[str, float]) -> dict[str, float]:
        total = self.total_value(prices)
        if total <= 0:
            return {t: 0.0 for t in TICKERS}
        return {t: self.holdings.get(t, 0) * float(prices[t]) / total for t in TICKERS}


def weights_from_scores(scores_df: pd.DataFrame) -> dict[str, float]:
    """Extrait {ticker: weight} depuis la sortie de compute_global_score()."""
    required = {"ticker", "weight"}
    if not required.issubset(scores_df.columns):
        raise ValueError("scores_df doit contenir les colonnes ticker et weight.")
    return {row["ticker"]: float(row["weight"]) for _, row in scores_df.iterrows()}


def _transaction_cost(value: float) -> float:
    return float(value) * TRANSACTION_COST_RATE


def allocate_initial(
    capital: float,
    target_weights: dict[str, float],
    prices: pd.Series | dict[str, float],
    day: str,
) -> tuple[PortfolioState, list[dict]]:
    """Allocation initiale depuis 100 % cash."""
    portfolio = PortfolioState(cash=float(capital), holdings={})
    transactions: list[dict] = []

    for ticker in TICKERS:
        weight = float(target_weights.get(ticker, 0.0))
        price = float(prices[ticker])
        target_value = capital * weight
        quantity = floor(target_value / price)
        if quantity <= 0:
            continue

        gross_value = quantity * price
        cost = gross_value + _transaction_cost(gross_value)
        if cost > portfolio.cash:
            quantity = floor(portfolio.cash / (price * (1 + TRANSACTION_COST_RATE)))
            gross_value = quantity * price
            cost = gross_value + _transaction_cost(gross_value)

        if quantity <= 0:
            continue

        portfolio.cash -= cost
        portfolio.holdings[ticker] = portfolio.holdings.get(ticker, 0) + quantity
        transactions.append({
            "date": day,
            "action": "BUY",
            "ticker": ticker,
            "shares": quantity,
            "price": round(price, 4),
            "value": round(gross_value, 2),
            "cost": round(_transaction_cost(gross_value), 2),
        })

    return portfolio, transactions


def rebalance_portfolio(
    previous: PortfolioState,
    target_weights: dict[str, float],
    prices: pd.Series | dict[str, float],
    day: str,
) -> tuple[PortfolioState, list[dict]]:
    """Rééquilibre le portefeuille J-1 vers les poids cibles de J."""
    total_value = previous.total_value(prices)
    target_shares: dict[str, int] = {}

    for ticker in TICKERS:
        weight = float(target_weights.get(ticker, 0.0))
        price = float(prices[ticker])
        target_shares[ticker] = floor((total_value * weight) / price)

    new_state = PortfolioState(cash=float(previous.cash), holdings=dict(previous.holdings))
    transactions: list[dict] = []

    # 1. Ventes d'abord.
    for ticker in TICKERS:
        current_qty = int(new_state.holdings.get(ticker, 0))
        target_qty = int(target_shares.get(ticker, 0))
        if current_qty <= target_qty:
            continue

        sell_qty = current_qty - target_qty
        price = float(prices[ticker])
        gross_value = sell_qty * price
        cost = _transaction_cost(gross_value)
        new_state.cash += gross_value - cost
        new_state.holdings[ticker] = target_qty
        if new_state.holdings[ticker] == 0:
            new_state.holdings.pop(ticker, None)

        transactions.append({
            "date": day,
            "action": "SELL",
            "ticker": ticker,
            "shares": sell_qty,
            "price": round(price, 4),
            "value": round(gross_value, 2),
            "cost": round(cost, 2),
        })

    # 2. Achats ensuite.
    for ticker in TICKERS:
        current_qty = int(new_state.holdings.get(ticker, 0))
        target_qty = int(target_shares.get(ticker, 0))
        if target_qty <= current_qty:
            continue

        wanted_qty = target_qty - current_qty
        price = float(prices[ticker])
        max_affordable = floor(new_state.cash / (price * (1 + TRANSACTION_COST_RATE)))
        buy_qty = min(wanted_qty, max_affordable)
        if buy_qty <= 0:
            continue

        gross_value = buy_qty * price
        cost = _transaction_cost(gross_value)
        new_state.cash -= gross_value + cost
        new_state.holdings[ticker] = new_state.holdings.get(ticker, 0) + buy_qty

        note = "cash_constrained" if buy_qty < wanted_qty else ""
        transactions.append({
            "date": day,
            "action": "BUY",
            "ticker": ticker,
            "shares": buy_qty,
            "price": round(price, 4),
            "value": round(gross_value, 2),
            "cost": round(cost, 2),
            "note": note,
        })

    return new_state, transactions
