import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_alpaca_news(tickers, from_date, to_date, output_csv_path, api_key, api_secret):
    """
    Récupère les actualités du marché via l'API Alpaca News
    pour une liste de tickers et les sauvegarde en CSV.
    """
    if api_key == "VOTRE_API_KEY_ICI" or not api_key:
        print("[Alpaca] Erreur : Clés API non configurées.")
        return

    print(f"[Alpaca] Lancement de l'extraction du {from_date} au {to_date}")
    
    # URL de l'API de données historiques de news d'Alpaca
    url = "https://data.alpaca.markets/v1beta1/news"
    
    # En-têtes requis pour l'authentification Alpaca
    headers = {
        "Apca-API-Key-Id": api_key,
        "Apca-API-Secret-Key": api_secret,
        "Accept": "application/json"
    }
    
    # Transformation de la liste de tickers en chaîne séparée par des virgules
    symbols_str = ",".join(tickers)
    
    params = {
        "symbols": symbols_str,
        "start": from_date,
        "end": to_date,
        "limit": 50 # Nombre de news maximum par requête
    }
    
    all_news = []
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            json_data = response.json()
            news_list = json_data.get("news", [])
            
            for item in news_list:
                # Alpaca renvoie une liste de symboles par news, on extrait le principal
                item_symbols = item.get("symbols", [])
                matched_ticker = item_symbols[0] if item_symbols else "UNKNOWN"
                
                all_news.append({
                    "ticker": matched_ticker,
                    "date": item.get("created_at"), # Déjà au format string ISO 8601
                    "source": item.get("source"),
                    "headline": item.get("headline"),
                    "summary": item.get("summary"),
                    "url": item.get("url")
                })
        else:
            print(f" [Erreur] Code {response.status_code} : {response.text}")
            
    except Exception as e:
        print(f" [Erreur] Échec de la requête Alpaca : {e}")
        
    # Traitement et sauvegarde
    if all_news:
        df = pd.DataFrame(all_news)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        
        # Sélection et ordre des colonnes
        df = df[['ticker', 'date', 'source', 'headline', 'summary', 'url']]
        
        # Création automatique du dossier de sortie s'il n'existe pas
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} actualités Alpaca stockées dans {output_csv_path}")
        print(df[['ticker', 'source', 'headline']].head(3))
    else:
        print("\n[Échec] Aucune actualité récupérée via Alpaca.")

if __name__ == "__main__":
    # Notre univers de recheche basé sur la hype
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # Dates au format RFC3339 requis par Alpaca (YYYY-MM-DDTHH:MM:SSZ)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=14) # Extraction sur les 14 derniers jours
    
    START_DATE_STR = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    END_DATE_STR = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Destination commune des fichiers bruts
    FILE_DESTINATION = "data_output/alpaca_news_raw.csv"
    
    # À remplacer par vos identifiants générés sur votre tableau de bord Alpaca
    ALPACA_KEY = "VOTRE_API_KEY_ICI"
    ALPACA_SECRET = "VOTRE_API_SECRET_ICI"
    
    fetch_alpaca_news(UNIVERS, START_DATE_STR, END_DATE_STR, FILE_DESTINATION, ALPACA_KEY, ALPACA_SECRET)