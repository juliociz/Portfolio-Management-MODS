# config.py
# ============================================================
# Paramètres globaux partagés par tous les modules du projet
# ============================================================

# ========================
# Univers d'investissement
# ========================
TICKERS = [
    "AAPL",   # Technologie
    "MSFT",   # Technologie (software/cloud)
    "JPM",    # Finance
    "XOM",    # Énergie
    "JNJ",    # Santé
]

# ========================
# Période d'analyse
# ========================
START_DATE = "2022-01-01"
END_DATE   = "2024-12-31"

# ========================
# Momentum
# ========================
MOMENTUM_WINDOWS = [1, 3, 6]  # en mois
MOMENTUM_WEIGHT  = 0.5        # poids dans le score global

# ========================
# Sentiment
# ========================
SENTIMENT_WEIGHT  = 0.5       # poids dans le score global
FINBERT_MODEL     = "ProsusAI/finbert"
MAX_TOKENS        = 512
NEWS_LOOKBACK_DAYS = 30       # jours de news à récupérer

# ========================
# NewsAPI
# ========================
NEWS_SOURCES = [
    "reuters",
    "bloomberg",
    "the-wall-street-journal",
    "cnbc",
]
NEWS_LANGUAGE = "en"

# ========================
# Backtesting
# ========================
INITIAL_CAPITAL    = 100_000   # en USD
REBALANCE_FREQ     = "M"       # M = mensuel, W = hebdomadaire
BENCHMARK_TICKER   = "^GSPC"   # S&P 500

# ========================
# Chemins
# ========================
DATA_RAW_PATH       = "data/raw/"
DATA_PROCESSED_PATH = "data/processed/"
