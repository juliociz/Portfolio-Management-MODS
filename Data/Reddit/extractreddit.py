import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone # Ajout de timezone pour corriger le warning

def fetch_reddit_via_pullpush(tickers, output_csv):
    print(f"[Reddit] Extraction via l'archive Pullpush pour : {tickers}")
    all_posts = []
    
    headers = {
        'User-Agent': 'TelecomParis-Student-Project/1.1'
    }
    
    subreddits_cibles = ["wallstreetbets", "stocks", "investing"]
    
    for ticker in tickers:
        print(f" -> Fouille des archives pour {ticker}...")
        
        for sub in subreddits_cibles:
            url = f"https://api.pullpush.io/reddit/search/submission/?q={ticker}&subreddit={sub}&size=20"
            
            # Système de sécurité : on essaie 3 fois max si on se prend une erreur 429
            max_tentatives = 3
            for tentative in range(max_tentatives):
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get('data', [])
                        
                        for post in posts:
                            texte_brut = post.get('selftext', "")
                            if texte_brut in ["[removed]", "[deleted]"]:
                                texte_brut = ""
                                
                            # Correction du Deprecation Warning avec la nouvelle norme Python
                            timestamp = post.get('created_utc', 0)
                            date_propre = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                                
                            all_posts.append({
                                "ticker": ticker,
                                "date": date_propre,
                                "subreddit": sub,
                                "title": post.get('title', "").replace('\n', ' '),
                                "text": texte_brut.replace('\n', ' '),
                                "url": f"https://www.reddit.com{post.get('permalink', '')}"
                            })
                        
                        # Si on arrive ici, c'est un succès, on sort de la boucle de tentative
                        break 
                        
                    elif response.status_code == 429:
                        print(f"   [Serveur saturé] Erreur 429. Pause de 10s (Tentative {tentative + 1}/{max_tentatives})...")
                        time.sleep(10) # On laisse le serveur respirer
                    else:
                        print(f"   [Erreur] Code {response.status_code} sur r/{sub}")
                        break # Si c'est une autre erreur, on ne s'acharne pas
                        
                except Exception as e:
                    print(f"   [Erreur réseau] Échec de connexion : {e}")
                    break
            
            # Pause standard augmentée (3 secondes) pour être sûr de ne pas brusquer l'API
            time.sleep(3)

    if all_posts:
        df = pd.DataFrame(all_posts)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        
        print(f"\n[Succès] {len(df)} posts Reddit extraits et stockés dans {output_csv}")
    else:
        print("\n[Échec] Aucun post récupéré.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    FILE_DESTINATION = "data_output/reddit_raw.csv"
    
    fetch_reddit_via_pullpush(UNIVERS, FILE_DESTINATION)