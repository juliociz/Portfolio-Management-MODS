import os
import time
import requests
import pandas as pd
from datetime import datetime

def fetch_reddit_via_pullpush(tickers, output_csv):
    print(f"[Reddit] Extraction via l'archive académique Pullpush pour : {tickers}")
    all_posts = []
    
    # Un User-Agent simple suffit ici
    headers = {
        'User-Agent': 'TelecomParis-Student-Project/1.0'
    }
    
    subreddits_cibles = ["wallstreetbets", "stocks", "investing"]
    
    for ticker in tickers:
        print(f" -> Fouille des archives pour {ticker}...")
        
        for sub in subreddits_cibles:
            # L'API Pullpush qui remplace celle de Reddit sans aucune restriction
            url = f"https://api.pullpush.io/reddit/search/submission/?q={ticker}&subreddit={sub}&size=20"
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # Pullpush renvoie les posts dans une liste 'data'
                    posts = data.get('data', [])
                    
                    for post in posts:
                        texte_brut = post.get('selftext', "")
                        
                        # On nettoie les posts supprimés par les modérateurs
                        if texte_brut in ["[removed]", "[deleted]"]:
                            texte_brut = ""
                            
                        all_posts.append({
                            "ticker": ticker,
                            "date": datetime.utcfromtimestamp(post.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            "subreddit": sub,
                            "title": post.get('title', "").replace('\n', ' '),
                            "text": texte_brut.replace('\n', ' '),
                            "url": f"https://www.reddit.com{post.get('permalink', '')}"
                        })
                else:
                    print(f"   [Erreur] Le serveur d'archive a répondu avec le code {response.status_code} sur r/{sub}")
                    
            except Exception as e:
                print(f"   [Erreur réseau] Échec de connexion sur le sub {sub} : {e}")
            
            # Petite pause polie pour respecter leurs serveurs gratuits
            time.sleep(1.5)

    # Sauvegarde au propre
    if all_posts:
        df = pd.DataFrame(all_posts)
        df['date'] = pd.to_datetime(df['date'])
        
        # Tri du plus récent au plus ancien
        df = df.sort_values(by='date', ascending=False)
        
        # Création du dossier et sauvegarde
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        
        print(f"\n[Succès] {len(df)} posts Reddit extraits et stockés dans {output_csv}")
        print(df[['ticker', 'subreddit', 'title']].head(3))
    else:
        print("\n[Échec] Aucun post récupéré.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    FILE_DESTINATION = "data_output/reddit_raw.csv"
    
    fetch_reddit_via_pullpush(UNIVERS, FILE_DESTINATION)