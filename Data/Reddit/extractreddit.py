import os
import time
import requests
import pandas as pd
import json # On importe la librairie JSON
from datetime import datetime, timezone

def fetch_reddit_industrial_json(tickers, output_csv1, output_json):
    print(f"[Big Data] Démarrage de l'extraction massive pour : {tickers}")
    all_posts = []
    
    headers = {
        'User-Agent': 'TelecomParis-Data-Engine/4.0'
    }
    
    subreddits_cibles = [
        "wallstreetbets", "stocks", "investing", 
        "StockMarket", "options", "Daytrading", 
        "ValueInvesting", "pennystocks", "dividends", "finance"
    ]
    
    PAGES_PER_SUB = 3 
    
    for ticker in tickers:
        print(f"\n -> Aspiration industrielle pour {ticker}...")
        
        for sub in subreddits_cibles:
            last_timestamp = "" 
            
            for page in range(PAGES_PER_SUB):
                url = f"https://api.pullpush.io/reddit/search/submission/?q={ticker}&subreddit={sub}&size=100"
                if last_timestamp:
                    url += f"&before={last_timestamp}"
                
                max_tentatives = 3
                success = False
                
                for tentative in range(max_tentatives):
                    try:
                        response = requests.get(url, headers=headers, timeout=20)
                        if response.status_code == 200:
                            posts = response.json().get('data', [])
                            if not posts:
                                break
                                
                            for post in posts:
                                texte_brut = post.get('selftext', "")
                                if texte_brut in ["[removed]", "[deleted]"]:
                                    texte_brut = ""
                                    
                                titre = post.get('title', "").replace('\n', ' ')
                                texte = texte_brut.replace('\n', ' ')
                                full_text = f"{titre}. {texte}".strip()
                                
                                if len(full_text) > 50:
                                    raw_timestamp = post.get('created_utc', 0)
                                    try:
                                        clean_timestamp = int(float(raw_timestamp))
                                        date_propre = datetime.fromtimestamp(clean_timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                                    except (ValueError, TypeError):
                                        continue 
                                        
                                    all_posts.append({
                                        "ticker": ticker,
                                        "date": date_propre,
                                        "subreddit": sub,
                                        "text": full_text,
                                        "url": f"https://www.reddit.com{post.get('permalink', '')}"
                                    })
                            
                            try:
                                last_timestamp = int(float(posts[-1].get('created_utc', 0)))
                            except (ValueError, TypeError):
                                break
                                
                            success = True
                            break 
                            
                        elif response.status_code == 429:
                            time.sleep(10)
                        else:
                            break
                            
                    except Exception as e:
                        print(f"   [Erreur] {e}")
                        break
                
                if not success:
                    break 
                
                time.sleep(2)

    if all_posts:
        # 1. Sauvegarde du CSV complet (Traceabilité)
        df = pd.DataFrame(all_posts)
        df = df.drop_duplicates(subset=['text'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        
        os.makedirs(os.path.dirname(output_csv1), exist_ok=True)
        df.to_csv(output_csv1, index=False, encoding='utf-8')
        
        # 2. Sauvegarde du JSON pour FinBERT (Exactement ton format)
        nlp_dict = {}
        for ticker in tickers:
            # On récupère tous les textes uniques pour un ticker donné
            textes_du_ticker = df[df['ticker'] == ticker]['text'].tolist()
            nlp_dict[ticker] = textes_du_ticker
            
        with open(output_json, 'w', encoding='utf-8') as f:
            # indent=4 permet de formater le fichier pour qu'il soit lisible par un humain
            json.dump(nlp_dict, f, ensure_ascii=False, indent=4)
        
        print(f"\n[SUCCÈS MASSIF] Extraction terminée !")
        print(f" -> {len(df)} posts uniques extraits.")
        print(f" -> Fichier de trace sauvegardé : {output_csv1}")
        print(f" -> Fichier JSON (Format NLP) sauvegardé : {output_json}")
    else:
        print("\n[Échec] Aucun post récupéré.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    FICHIER_COMPLET = "data_output/reddit_raw.csv"
    # Attention, on a changé l'extension en .json !
    FICHIER_JSON_NLP = "data_output/reddit_raw2.json" 
    
    fetch_reddit_industrial_json(UNIVERS, FICHIER_COMPLET, FICHIER_JSON_NLP)