import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_finnhub_news(tickers, output_csv, api_key):
    # Sécurité anti-tête en l'air
    if not api_key or api_key == "METTRE_VOTRE_CLE_ICI":
        print("[Finnhub] ERREUR : Tu dois insérer ta vraie clé API Finnhub dans le code !")
        return

    print(f"[Finnhub] Extraction des dépêches (30 derniers jours) pour : {tickers}")
    all_news = []
    
    # Finnhub demande le format YYYY-MM-DD
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    for ticker in tickers:
        print(f" -> Interrogation de l'API pour {ticker}...")
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start_date}&to={end_date}&token={api_key}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                news_list = response.json()
                for item in news_list:
                    all_news.append({
                        "ticker": ticker,
                        "date": item.get("datetime"),
                        "source": item.get("source"),
                        "headline": item.get("headline", "").replace('\n', ' '),
                        "summary": item.get("summary", "").replace('\n', ' '),
                        "url": item.get("url")
                    })
            elif response.status_code == 429:
                print(" [Erreur] Limite de requêtes atteinte (Rate Limit Finnhub).")
            else:
                print(f" [Erreur] Code {response.status_code}")
        except Exception as e:
            print(f" [Erreur réseau] Échec sur {ticker}: {e}")
            
        time.sleep(1) # Le plan gratuit Finnhub limite à 60 requêtes/minute
        
    if all_news:
        df = pd.DataFrame(all_news)
        # Conversion du timestamp UNIX Finnhub en vraie date
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df = df.sort_values(by='date', ascending=False)
        
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} vrais articles Finnhub sauvegardés dans {output_csv}")
    else:
        print("\n[Échec] Aucune actualité récupérée.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # ⚠️ METS TA VRAIE CLÉ FINNHUB ENTRE LES GUILLEMETS ICI ⚠️
    API_KEY = "METTRE_VOTRE_CLE_ICI" 
    
    fetch_finnhub_news(UNIVERS, "data_output/finnhub_news_raw.csv", API_KEY)ION, API_KEY)