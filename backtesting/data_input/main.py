import os
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import pandas_market_calendars as mcal

from alpha_vantage_news import get_finbert_ready_news


# ============================================================
# Chargement du .env
# ============================================================

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

ALPHA_VANTAGE_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# ============================================================
# Liste des entreprises
# ============================================================

stocks = [
    {"name": "Nike", "ticker": "NKE"},
    {"name": "Target", "ticker": "TGT"},
    {"name": "Disney", "ticker": "DIS"},
    {"name": "Starbucks", "ticker": "SBUX"},
    {"name": "Tesla", "ticker": "TSLA"}
]

# ============================================================
# Calendrier NYSE - Mai 2025
# ============================================================

nyse = mcal.get_calendar("NYSE")

trading_days = nyse.schedule(
    start_date="2025-05-01",
    end_date="2025-05-31"
).index

print(f"{len(trading_days)} séances détectées en mai 2025.\n")

# ============================================================
# Dossier principal
# ============================================================

base_output_dir = Path("AlphaVantage_Backtest")

# ============================================================
# Boucle principale
# ============================================================

total_requests = len(trading_days) * len(stocks)
current_request = 0

for trading_day in trading_days:

    trading_day = trading_day.to_pydatetime()

    print(
        f"\n==============================="
        f"\nTrading Day : {trading_day.date()}"
        f"\n===============================\n"
    )

    for stock in stocks:

        current_request += 1

        ticker = stock["ticker"]
        company_name = stock["name"]

        print(
            f"[{current_request}/{total_requests}] "
            f"{ticker} - {trading_day.date()}"
        )

        try:

            get_finbert_ready_news(
                ticker=ticker,
                company_name=company_name,
                target_date=trading_day,
                api_key=ALPHA_VANTAGE_KEY,
                output_dir=base_output_dir / ticker
            )

        except Exception as e:

            print(
                f"Erreur pour {ticker} "
                f"le {trading_day.date()} : {e}"
            )

        # Respect du quota Alpha Vantage gratuit
        if current_request < total_requests:
            print("Attente 15 secondes...")
            time.sleep(15)

print("\nTéléchargement terminé.")