import json
import os 
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from newsapi import NewsApiClient

# GESTION DU CHEMIN : On force la recherche du .env à la racine du projet
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 1. Connexion à l'API via la clé sécurisée du fichier .env
NEWS_API_KEY = os.getenv("MY_NEWS_API_KEY")
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# 2. CALCUL DE LA DATE (Maximum 7 jours en arrière)
date_limite = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# LA LISTE DES 5 ENTREPRISES
stocks = [
    {"name": "Nike", "ticker": "NKE"},
    {"name": "Target", "ticker": "TGT"},
    {"name": "Disney", "ticker": "DIS"},
    {"name": "Starbucks", "ticker": "SBUX"},
    {"name": "Tesla", "ticker": "TSLA"}
]

# Liste noire générale pour éliminer les blogs de tests ou comparatifs inutiles
blacklist = ["review", "unboxing", "versus", "vs"]

print(f"Lancement de la récupération des articles (depuis le {date_limite})...\n")

# 3. BOUCLE SUR CHAQUE ENTREPRISE
for stock in stocks:
    name = stock["name"]
    ticker = stock["ticker"]
    
    print(f"Traitement de {name} ({ticker})...")
    
    # Requête de recherche : Nom de la marque OU Ticker boursier + mots-clés financiers obligatoires
    query_finance = f'("{name}" OR "{ticker}") AND (stock OR earnings OR financial OR shares OR market)'
    
    try:
        response = newsapi.get_everything(
            q=query_finance,
            language="en",
            sort_by="relevancy",       # Classement par pertinence financière
            from_param=date_limite,    # Blocage strict à J-7 maximum
            page_size=30               # On en prend 30 pour appliquer nos filtres après
        )
        
        finbert_ready_data = {
            "ticker": ticker,
            "company_name": name,
            "date_filter": f"Last 7 days (since {date_limite})",
            "articles": []
        }
        
        for art in response["articles"]:
            # On ignore l'article s'il manque le titre ou la description
            if not art["title"] or not art["description"]:
                continue
            
            # Filtrage anti-pollution textuelle
            text_content = f"{art['title']} {art['description']}".lower()
            if any(bad_word in text_content for bad_word in blacklist):
                continue
            
            # FUSION TITRE + DESCRIPTION : Format parfait pour FinBERT
            full_text_signal = f"{art['title']}. {art['description']}"
            
            finbert_ready_data["articles"].append({
                "source": art["source"]["name"],
                "date": art["publishedAt"],
                "text_to_analyze": full_text_signal  
            })
            
            # Blocage strict à maximum 15 articles par entreprise
            if len(finbert_ready_data["articles"]) == 15:
                break
        
        # 4. SAUVEGARDE AUTOMATIQUE DANS LE DOSSIER 'src/data/'
        output_dir = Path(__file__).resolve().parent
        output_file = output_dir / f"{ticker.lower()}_for_finbert.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(finbert_ready_data, f, ensure_ascii=False, indent=4)
            
        print(f"Fichier '{output_file.name}' généré avec {len(finbert_ready_data['articles'])} articles.\n")
        
    except Exception as e:
        print(f"Erreur lors de la récupération pour {name} : {e}\n")

print("Opération terminée ! Tes 5 fichiers JSON sont prêts et nettoyés.")