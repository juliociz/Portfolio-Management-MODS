import os
import time
import requests
import pandas as pd

def fetch_stocktwits_feed(tickers, output_csv_path):
    """
    Récupère les 30 derniers messages en temps réel sur StockTwits 
    pour une liste de tickers et les sauvegarde dans un fichier CSV.
    """
    print(f"[StockTwits] Lancement de l'extraction pour : {tickers}")
    all_data = []
    
    # En-tête standard pour éviter les blocages de sécurité basiques
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for ticker in tickers:
        print(f" -> Extraction du flux pour {ticker}...")
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                json_data = response.json()
                messages = json_data.get("messages", [])
                
                for msg in messages:
                    # Extraction du sentiment utilisateur si disponible (Bullish/Bearish)
                    user_sentiment = None
                    entities = msg.get("entities", {})
                    if entities and entities.get("sentiment"):
                        user_sentiment = entities["sentiment"].get("basic")
                    
                    # Stockage des champs essentiels pour FinBERT
                    all_data.append({
                        "ticker": ticker,
                        "date": msg.get("created_at"),
                        "message_id": msg.get("id"),
                        "username": msg.get("user", {}).get("username"),
                        "sentiment_declare": user_sentiment,
                        "text": msg.get("body")
                    })
            else:
                print(f" [Attention] Impossible de récupérer {ticker}. Code erreur : {response.status_code}")
                
        except Exception as e:
            print(f" [Erreur] Problème de connexion pour le ticker {ticker} : {e}")
            
        # Pause réglementaire de 2 secondes entre chaque requête API
        time.sleep(2)
        
    # Création du DataFrame et sauvegarde
    if all_data:
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Création automatique du dossier parent s'il n'existe pas encore
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        # Sauvegarde au format CSV
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"\n[Succès] {len(df)} messages stockés dans {output_csv_path}")
        print(df[['ticker', 'sentiment_declare', 'text']].head(3))
    else:
        print("\n[Échec] Aucun message n'a pu être récupéré.")

if __name__ == "__main__":
    # Notre univers d'étude basé sur la "hype" et l'e-réputation
    UNIVERS_REPUTATION = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # Définition du chemin de sortie (s'aligne avec la racine du projet)
    # Sauvegarde dans un dossier racine 'data_output' pour que l'équipe y ait accès
    FILE_DESTINATION = "data_output/stocktwits_raw.csv"
    
    # Exécution du script
    fetch_stocktwits_feed(UNIVERS_REPUTATION, FILE_DESTINATION)