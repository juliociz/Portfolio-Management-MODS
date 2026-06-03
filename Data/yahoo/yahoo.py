import os
import time
import yfinance as yf
import pandas as pd

def fetch_yahoo_news(tickers, output_csv_path):
    """
    Récupère les dernières actualités disponibles sur Yahoo Finance
    pour une liste de tickers et les sauvegarde dans un fichier CSV.
    """
    print(f"[Yahoo Finance] Lancement de l'extraction pour : {tickers}")
    all_news = []
    
    for ticker in tickers:
        print(f" -> Extraction des actualités pour {ticker}...")
        try:
            # Initialisation du ticker yfinance
            asset = yf.Ticker(ticker)
            news_list = asset.news
            
            if news_list:
                for item in news_list:
                    all_news.append({
                        "ticker": ticker,
                        "timestamp": item.get("providerPublishTime"),
                        "title": item.get("title"),
                        "publisher": item.get("publisher"),
                        "link": item.get("link"),
                        "type": item.get("type")
                    })
            else:
                print(f" [Attention] Aucune news trouvée pour {ticker}.")
                
        except Exception as e:
            print(f" [Erreur] Impossible de récupérer les news pour {ticker} : {e}")
            
        # Petite pause de sécurité entre chaque ticker
        time.sleep(1)
        
    # Traitement et sauvegarde des données
    if all_news:
        df = pd.DataFrame(all_news)
        
        # Conversion du timestamp Unix en vraie date lisible
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Tri par date de la plus récente à la plus ancienne
        df = df.sort_values(by='date', ascending=False)
        
        # Sélection des colonnes utiles pour la partie sentiment
        df = df[['ticker', 'date', 'publisher', 'title', 'link']]
        
        # Création automatique du dossier data_output s'il n'existe pas
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        # Sauvegarde au format CSV
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} actualités stockées dans {output_csv_path}")
        print(df[['ticker', 'publisher', 'title']].head(3))
    else:
        print("\n[Échec] Aucune actualité n'a pu être récupérée.")

if __name__ == "__main__":
    # Notre univers basé sur la réputation
    UNIVERS_REPUTATION = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # Destination des données partagées à la racine
    FILE_DESTINATION = "data_output/yahoo_news_raw.csv"
    
    # Exécution du script
    fetch_yahoo_news(UNIVERS_REPUTATION, FILE_DESTINATION)