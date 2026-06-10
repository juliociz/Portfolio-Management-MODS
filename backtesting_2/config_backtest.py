"""
config_backtest.py

Centralise tous les paramètres du backtest PyPortfolioOpt.

Ce dossier est volontairement indépendant du reste du repository :
- aucun import depuis portfolio_manag/
- aucun import depuis Traitement/
- toutes les constantes et fonctions nécessaires au backtest sont dans backtesting_2/
"""

from pathlib import Path

# ── Univers d'investissement ──────────────────────────────────────────────────
TICKERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]

# ── Dates du backtest ─────────────────────────────────────────────────────────
BACKTEST_START = "2026-05-01"
BACKTEST_END = "2026-05-31"

# ── Capital notionnel ─────────────────────────────────────────────────────────
INITIAL_CAPITAL = 100_000.0

# ── Pondération des signaux ───────────────────────────────────────────────────
SENTIMENT_WEIGHT = 0.5
MOMENTUM_WEIGHT = 0.5

# ── Fenêtres de momentum (en mois) ────────────────────────────────────────────
MOMENTUM_WINDOWS = [1, 3]          # V1 ; ajouter 6 si historique disponible
TRADING_DAYS_PER_MONTH = 21

# ── PyPortfolioOpt ────────────────────────────────────────────────────────────
SIGNAL_STRENGTH = 0.10             # +10 % annualisé par unité de global_score
RISK_LAMBDA = 0.20                 # facteur d'amplification du risque (V2 optionnelle)
WEIGHT_BOUNDS = (0.0, 0.40)        # min / max par ticker
RISK_FREE_RATE = 0.02              # taux sans risque annuel (2 %)
FREQUENCY = 252                    # jours de trading par an

# ── Prix ──────────────────────────────────────────────────────────────────────
# Pour un backtest sur mai 2026 avec momentum 1m/3m, on prend un historique
# dès janvier 2026. Si MOMENTUM_WINDOWS contient 6, passer à 2025-10-01 environ.
PRICE_START = "2026-01-01"
PRICE_END = "2026-06-01"

# Source de prix :
# - "yahoo" : recommandé pour un test autonome sans clé API
# - "alphavantage" : nécessite ALPHAVANTAGE_API_KEY dans l'environnement
PRICE_SOURCE = "yahoo"

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_INPUT = BASE_DIR / "data_input"
DATA_OUTPUT = BASE_DIR / "data_output"
RESULTS_DIR = BASE_DIR / "results"

PRICES_CSV = DATA_OUTPUT / "prices_backtest.csv"
SENTIMENT_OUT_CSV = DATA_OUTPUT / "daily_sentiment_scores.csv"
MOMENTUM_OUT_CSV = DATA_OUTPUT / "daily_momentum_scores.csv"
GLOBAL_SCORES_CSV = DATA_OUTPUT / "daily_global_scores.csv"
WEIGHTS_CSV = DATA_OUTPUT / "daily_weights.csv"

PORTFOLIO_RET_CSV = RESULTS_DIR / "portfolio_returns.csv"
WEIGHTS_HIST_CSV = RESULTS_DIR / "weights_history.csv"
SUMMARY_JSON = RESULTS_DIR / "summary.json"
BACKTEST_CHART_PNG = RESULTS_DIR / "backtest_chart.png"
