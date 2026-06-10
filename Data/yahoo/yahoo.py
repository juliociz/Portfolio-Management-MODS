import os
import time
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

def fetch_yahoo_rss_news(tickers, output_csv):
    print(f"[Yahoo] Récupération des articles via flux RSS officiel pour : {tickers}")
    all_news = []
    
    # On simule un navigateur pour éviter les blocages
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for ticker in tickers:
        print(f" -> Aspiration des news pour {ticker}...")
        # L'URL RSS officielle de Yahoo Finance pour un ticker donné
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Analyse du fichier XML renvoyé par Yahoo
                root = ET.fromstring(response.text)
                
                # On boucle sur chaque article (<item>)
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    
                    # Conversion de la date RSS en vrai format Date lisible
                    try:
                        dt = parsedate_to_datetime(pub_date_str)
                    except:
                        dt = None

                    all_news.append({
                        "ticker": ticker,
                        "date": dt,
                        "publisher": "Yahoo Finance", 
                        "title": title,
                        "link": link
                    })
            else:
                print(f" [Erreur] Serveur Yahoo a répondu avec le code {response.status_code}")
                
        except Exception as e:
            print(f" [Erreur] Échec de l'extraction sur {ticker}: {e}")
        
        # Petite pause pour ne pas surcharger le serveur
        time.sleep(1)

    # Création du CSV final
    if all_news:
        df = pd.DataFrame(all_news)
        
        # Nettoyage et tri par date
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.sort_values(by='date', ascending=False)
        
        # Création du dossier et sauvegarde
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        
        print(f"\n[Succès] {len(df)} vrais articles extraits et sauvegardés dans {output_csv}")
        # Affichage de contrôle dans le terminal pour te rassurer
        print(df[['ticker', 'title']].head(5))
    else:
        print("\n[Échec] Aucun article récupéré.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    FILE_DESTINATION = "data_output/yahoo_news_raw.csv"
    
    fetch_yahoo_rss_news(UNIVERS, FILE_DESTINATION)