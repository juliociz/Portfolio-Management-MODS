import os
import time
import requests
import pandas as pd

def fetch_stocktwits_feed(tickers, output_csv):
    print(f"[StockTwits] Extraction des vrais messages pour : {tickers}")
    all_messages = []
    
    # Obligatoire pour ne pas se faire bloquer par le pare-feu de StockTwits
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for ticker in tickers:
        print(f" -> Connexion au flux {ticker}...")
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                messages = response.json().get("messages", [])
                
                for msg in messages:
                    # On cherche le tag "Bullish" ou "Bearish" si l'utilisateur l'a mis
                    sentiment = None
                    if msg.get("entities") and msg.get("entities").get("sentiment"):
                        sentiment = msg["entities"]["sentiment"].get("basic")
                        
                    all_messages.append({
                        "ticker": ticker,
                        "date": msg.get("created_at"),
                        "username": msg.get("user", {}).get("username", "Anonyme"),
                        "text": msg.get("body", "").replace('\n', ' '), # On vire les sauts de ligne qui cassent les CSV
                        "sentiment_declare": sentiment
                    })
            else:
                print(f" [Erreur] Rejeté par StockTwits (Code {response.status_code})")
        except Exception as e:
            print(f" [Erreur réseau] Impossible de joindre StockTwits pour {ticker}")
            
        time.sleep(2) # On respire pour ne pas se faire bannir l'IP
        
    if all_messages:
        df = pd.DataFrame(all_messages)
        df['date'] = pd.to_datetime(df['date'])
        
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} vrais tweets boursiers sauvegardés dans {output_csv}")
    else:
        print("\n[Échec] Aucun message récupéré. Le CSV n'a pas été créé pour éviter d'écraser les données.")

if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    fetch_stocktwits_feed(UNIVERS, "data_output/stocktwits_raw.csv")