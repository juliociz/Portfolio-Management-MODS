"""
Configuration du backtest V1 sur mai 2026.

Le backtest suppose qu'un fichier JSON existe pour chaque jour de décision :
    backtesting/data_input/alphavantage_merged_YYYYMMDD.json

Chaque fichier doit contenir les articles disponibles pour la décision du jour,
par exemple les articles de la fenêtre J-5 déjà préparés en amont.
"""
from pathlib import Path

TICKERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]

BACKTEST_START = "2026-05-01"
BACKTEST_END = "2026-05-31"

INITIAL_CAPITAL = 100_000.0

SENTIMENT_WEIGHT = 0.5
MOMENTUM_WEIGHT = 0.5

# Fenêtres en mois, cohérentes avec le projet initial.
# Le module portfolio_manag.momentum.momentum interprète 1 comme environ 21 jours de trading.
MOMENTUM_WINDOWS = [1, 3]

# Convention V1 : pas de frais, pas de slippage.
TRANSACTION_COST_RATE = 0.0

DATA_INPUT_DIR = Path("backtesting/data_input")
DATA_OUTPUT_DIR = Path("backtesting/data_output")
RESULTS_DIR = Path("backtesting/results")

ARTICLE_FILE_PREFIX = "alphavantage_merged_"
ARTICLE_FILE_PATTERN = "alphavantage_merged_{date}.json"
