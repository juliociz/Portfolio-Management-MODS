import os
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import pandas_market_calendars as mcal

from alphavantage import get_finbert_ready_news

# ============================================================
# Chargement des clés API
# ============================================================

load_dotenv()

API_KEYS = [
    os.getenv("ALPHAVANTAGE_API_KEY_1"),
    os.getenv("ALPHAVANTAGE_API_KEY_2"),
    os.getenv("ALPHAVANTAGE_API_KEY_3"),
    os.getenv("ALPHAVANTAGE_API_KEY_4"),
]

# On enlève les clés vides éventuelles
API_KEYS = [key for key in API_KEYS if key]

if not API_KEYS:
    raise ValueError("Aucune clé Alpha Vantage trouvée.")

# ============================================================
# Liste des entreprises
# ============================================================

stocks = [
    #{"name": "Nike", "ticker": "NKE"},
    #{"name": "Target", "ticker": "TGT"},
    #{"name": "Disney", "ticker": "DIS"},
    {"name": "Starbucks", "ticker": "SBUX"},
    #{"name": "Tesla", "ticker": "TSLA"}
]

# ============================================================
# Calendrier NYSE - Mai 2025
# ============================================================

nyse = mcal.get_calendar("NYSE")

trading_days = nyse.schedule(
    start_date="2026-02-01",
    end_date="2026-02-28"
).index

print(f"{len(trading_days)} séances détectées.")

# ============================================================
# Dossier de sortie
# ============================================================

base_output_dir = Path("AlphaVantage_Backtest")

# ============================================================
# Rotation des clés
# ============================================================

key_index = 0

total_requests = len(trading_days) * len(stocks)
current_request = 0

for trading_day in trading_days:

    trading_day = trading_day.to_pydatetime()
    
    # 🛑 Sécurité brute : On ignore les jours strictement inférieurs au 6 mai
    #if trading_day.date() < datetime(2026, 2, 23).date():
    #    current_request += len(stocks) # On met à jour le compteur global pour l'affichage
    #    continue

    print(
        f"\n==============================\n"
        f"Trading Day : {trading_day.date()}\n"
        f"=============================="
    )

    for stock in stocks:

        current_request += 1

        current_key = API_KEYS[key_index]
        key_index = (key_index + 1) % len(API_KEYS)

        ticker = stock["ticker"]
        company_name = stock["name"]

        print(
            f"[{current_request}/{total_requests}] "
            f"{ticker} | clé {(key_index if key_index != 0 else len(API_KEYS))}"
        )

        try:

            get_finbert_ready_news(
                ticker=ticker,
                company_name=company_name,
                target_date=trading_day,
                api_key=current_key,
                output_dir=base_output_dir / ticker
            )

        except Exception as e:

            print(
                f"Erreur pour {ticker} "
                f"le {trading_day.date()} : {e}"
            )

        # Limite Alpha Vantage :
        # 5 requêtes/minute par clé
        time.sleep(15)

print("\nTéléchargement terminé.")