import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_alpaca_news(tickers, output_csv, api_key, api_secret):
    if not api_key or api_key == "METTRE_KEY_ID_ICI":
        print("[Alpaca] ERREUR : Tu dois insérer tes vraies clés API Alpaca dans le code !")
        return

    print(f"[Alpaca] Extraction des actualités de marché pour : {tickers}")
    all_news = []
    
    url = "https://data.alpaca.markets/v1beta1/news"
    headers = {
        "Apca-API-Key-Id": api_key,
        "Apca-API-Secret-Key": api_secret,
        "Accept": "application/json"
    }
    
    # Alpaca demande le format RFC3339
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=14)
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Alpaca permet de demander plusieurs tickers d'un coup
    symbols_str = ",".join(tickers)
    params = {
        "symbols": symbols_str,
        "start": start_str,
        "end": end_str,
        "limit": 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            news_list = response.json().get("news", [])
            for item in news_list:
                # Alpaca liste tous les tickers mentionnés, on prend le premier
                symbols_mentioned = item.get("symbols", ["UNKNOWN"])
                primary_ticker = symbols_mentioned[0] if symbols_mentioned else "UNKNOWN"
                
                # On s'assure qu'on ne garde que les tickers de notre univers
                if primary_ticker in tickers:
                    all_news.append({
                        "ticker": primary_ticker,
                        "date": item.get("created_at"),
                        "source": item.get("source"),
                        "headline": item.get("headline", "").replace('\n', ' '),
                        "summary": item.get("summary", "").replace('\n', ' '),
                        "url": item.get("url")
                    })
        else:
            print(f" [Erreur] Refusé par Alpaca. Vérifie tes clés. (Code {response.status_code})")
            
    except Exception as e:
        print(f" [Erreur réseau] Échec de la requête Alpaca : {e}")
        
    if all_news:
        df = pd.DataFrame(all_news)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} actualités Alpaca sauvegardées dans {output_csv}")
    else:
        print("\n[Échec] Aucune actualité récupérée.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # ⚠️ METS TES VRAIES CLÉS ALPACA (PAPER TRADING) ICI ⚠️
    ALPACA_KEY = "METTRE_KEY_ID_ICI"
    ALPACA_SECRET = "METTRE_SECRET_KEY_ICI"
    
    fetch_alpaca_news(UNIVERS, "data_output/alpaca_news_raw.csv", ALPACA_KEY, ALPACA_SECRET)















    