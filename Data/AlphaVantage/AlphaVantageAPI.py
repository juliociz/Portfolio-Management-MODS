import json
import os 
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

# GESTION DU CHEMIN : On force la recherche du .env à la racine du projet
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 1. Récupération de la clé API Alpha Vantage spécifique depuis le .env
ALPHA_VANTAGE_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# LA LISTE DES 5 ENTREPRISES
stocks = [
    {"name": "Nike", "ticker": "NKE"},
    {"name": "Target", "ticker": "TGT"},
    {"name": "Disney", "ticker": "DIS"},
    {"name": "Starbucks", "ticker": "SBUX"},
    {"name": "Tesla", "ticker": "TSLA"}
]

print("Lancement de la récupération des articles financiers via Alpha Vantage...\n")

# CRÉATION DU DOSSIER DE DESTINATION SPÉCIFIQUE SI ABSENT
output_dir = Path(__file__).resolve().parent / "AlphaVantageàtraiter"
output_dir.mkdir(parents=True, exist_ok=True)

# 2. BOUCLE SUR CHAQUE ENTREPRISE
for index, stock in enumerate(stocks):
    name = stock["name"]
    ticker = stock["ticker"]
    
    print(f"Traitement de {name} ({ticker})...")
    
    # URL de l'API Alpha Vantage pour les actualités et le sentiment
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,            # Filtre directement par le ticker boursier officiel
        "sort": "LATEST",             # Récupère les articles les plus récents
        "limit": 50,                  # On demande 50 articles pour filtrer ensuite
        "apikey": ALPHA_VANTAGE_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # Sécurité si l'API renvoie une erreur de quota ou de clé
        if "feed" not in data:
            print(f"Impossible de récupérer les données pour {ticker}. Message API : {data.get('Information', 'Erreur inconnue')}")
            continue
            
        finbert_ready_data = {
            "ticker": ticker,
            "company_name": name,
            "articles": []
        }
        
        # 3. TRAITEMENT ET FILTRAGE DES ARTICLES
        for item in data["feed"]:
            title = item.get("title")
            summary = item.get("summary")
            
            if not title or not summary:
                continue
                
            # Vérification de la pertinence de l'article pour NOTRE ticker
            ticker_relevance = 0.0
            for ticker_info in item.get("ticker_sentiment", []):
                if ticker_info["ticker"] == ticker:
                    ticker_relevance = float(ticker_info["relevance_score"])
                    break
            
            # FILTRE STRICT : On ne garde l'article que si notre entreprise est un sujet majeur (pertinence > 35%)
            if ticker_relevance < 0.35:
                continue
                
            # Stockage des données propres pour FinBERT
            finbert_ready_data["articles"].append({
                "source": item.get("source"),
                "date": item.get("time_published"),
                "title": title,
                "summary": summary,
                "text_to_analyze": f"{title}. {summary}",
                "alpha_vantage_sentiment_label": item.get("overall_sentiment_label"), # Permet de comparer avec FinBERT
                "ticker_relevance_score": ticker_relevance
            })
            
            # Blocage strict à maximum 15 articles par entreprise
            if len(finbert_ready_data["articles"]) == 15:
                break
                
        # 4. SAUVEGARDE DANS LE DOSSIER 'AlphaVantageàtraiter'
        output_file = output_dir / f"{ticker.lower()}_for_finbert.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(finbert_ready_data, f, ensure_ascii=False, indent=4)
            
        print(f"Fichier '{output_file.name}' généré avec {len(finbert_ready_data['articles'])} articles financiers dans {output_dir.name}/.\n")
        
    except Exception as e:
        print(f"Erreur réseau pour {name} : {e}\n")
        
    # GESTION DU QUOTA DE L'API GRATUITE (Max 5 requêtes par minute)
    # On attend 15 secondes entre chaque entreprise, sauf pour la dernière
    if index < len(stocks) - 1:
        print("Attente de 15 secondes pour respecter les limites de l'API Alpha Vantage...")
        time.sleep(15)

print(f"\nOpération terminée ! Vos fichiers JSON sont disponibles dans le dossier '{output_dir.name}'.")