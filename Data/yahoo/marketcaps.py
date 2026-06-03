import os
import yfinance as yf
import pandas as pd

def fetch_market_caps(tickers, output_csv_path):
    """
    Extrait proprement la capitalisation boursière actuelle des entreprises
    sans toucher aux autres scripts de prix.
    """
    print(f"[M1 - Market Caps] Extraction pour l'univers : {tickers}")
    caps_data = []
    
    for ticker in tickers:
        try:
            asset = yf.Ticker(ticker)
            # On récupère la valeur brute de la capitalisation boursière
            market_cap = asset.info.get("marketCap", None)
            
            if market_cap:
                caps_data.append({
                    "ticker": ticker,
                    "market_cap": market_cap
                })
                print(f" -> {ticker} : {market_cap:,} USD")
            else:
                print(f" [Attention] Pas de donnée pour {ticker}")
        except Exception as e:
            print(f" [Erreur] Impossible de récupérer la capitalisation de {ticker} : {e}")
            
    # Sauvegarde si on a récupéré des données
    if caps_data:
        df = pd.DataFrame(caps_data)
        
        # Création du dossier data_output s'il n'existe pas
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        df.to_csv(output_csv_path, index=False)
        print(f"\n[Succès] Fichier sauvegardé dans : {output_csv_path}")
    else:
        print("\n[Échec] Aucune donnée n'a pu être extraite.")

if __name__ == "__main__":
    # Notre univers basé sur la réputation
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    
    # Destination des données partagées à la racine
    FILE_DESTINATION = "data_output/market_caps.csv"
    
    fetch_market_caps(UNIVERS, FILE_DESTINATION)