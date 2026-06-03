import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_finnhub_news(tickers, from_date, to_date, output_csv_path, api_token):
    """
    Récupère les actualités d'entreprises sur Finnhub entre deux dates
    et les sauvegarde dans un fichier CSV.
    """
    if api_token == "VOTRE_CLE_FINNHUB_ICI" or not api_token:
        print("[Finnhub] Erreur : Vous devez insérer une clé API valide.")
        return

    print(f"[Finnhub] Lancement de l'extraction du {from_date} au {to_date} pour : {tickers}")
    all_news = []
    
    for ticker in tickers:
        print(f" -> Extraction des news pour {ticker}...")
        
        # Endpoint de Finnhub pour les news d'une entreprise specifique
        url = "https://finnhub.io/api/v1/company-news"
        
        params = {
            "symbol": ticker,
            "from": from_date,
            "to": to_date,
            "token": api_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                news_list = response.json()
                
                for item in news_list:
                    all_news.append({
                        "ticker": ticker,
                        "timestamp": item.get("datetime"), # Timestamp Unix
                        "headline": item.get("headline"), # Titre principal
                        "summary": item.get("summary"),   # Resume de l'article
                        "source": item.get("source"),     # Source (ex: Reuters)
                        "url": item.get("url")
                    })
                print(f"    -> {len(news_list)} articles trouves.")
            elif response.status_code == 429:
                print(" [Attention] Limite de requetes atteinte (Rate limit). Pause requise.")
                time.sleep(30)
            else:
                print(f" [Attention] Code erreur {response.status_code} pour {ticker}")
                
        except Exception as e:
            print(f" [Erreur] Connexion impossible pour {ticker} : {e}")
            
        # Pause de 1 seconde entre chaque requete pour respecter le plan gratuit
        time.sleep(1)
        
    # Traitement et sauvegarde
    if all_news:
        df = pd.DataFrame(all_news)
        
        # Conversion du timestamp Unix en date lisible
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values(by='date', ascending=False)
        
        # Organisation des colonnes pour le traitement FinBERT
        df = df[['ticker', 'date', 'source', 'headline', 'summary', 'url']]
        
        # Creation du dossier de sortie si besoin
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} news Finnhub stockées dans {output_csv_path}")
        print(df[['ticker', 'source', 'headline']].head(3))
    else:
        print("\n[Échec] Aucune actualité récupérée.")

if __name__ == "__main__":
    # Univers de l'e-reputation
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # Pour le test, on prend les 30 derniers jours (le plan gratuit bloque parfois l'historique lointain)
    end_dt = datetime.today()
    start_dt = end_dt - timedelta(days=30)
    
    START_DATE_STR = start_dt.strftime("%Y-%m-%d")
    END_DATE_STR = end_dt.strftime("%Y-%m-%d")
    
    # Placement du CSV dans votre dossier partage commun
    FILE_DESTINATION = "data_output/finnhub_news_raw.csv"
    
    # Mettez votre cle API gratuite recuperee sur finnhub.io ici
    # (Ou configurez-la pour lire votre fichier .env si vous savez faire)
    API_KEY = "VOTRE_CLE_FINNHUB_ICI"
    
    fetch_finnhub_news(UNIVERS, START_DATE_STR, END_DATE_STR, FILE_DESTINATION, API_KEY)