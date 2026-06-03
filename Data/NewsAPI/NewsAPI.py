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

# 📰 WHITELIST DES SOURCES FINANCIÈRES LÉGITIMES (Seuls ces médias seront acceptés)
# Mise à jour de la liste des sources avec 24/7 Wall St.
financial_sources = [
    "reuters", "bloomberg", "cnbc", "forbes", "business insider", "the wall street journal", 
    "wsj", "financial times", "ft", "yahoo finance", "marketwatch", "investing.com", 
    "seeking alpha", "the motley fool", "benzinga", "barron's", "investor's business daily",
    "24/7 wall st"  
]

print(f"Lancement de la récupération des articles (depuis le {date_limite})...\n")

# CRÉATION DU DOSSIER DE DESTINATION SI ABSENT
output_dir = Path(__file__).resolve().parent / "NewsAPIàtraiter"
output_dir.mkdir(parents=True, exist_ok=True)

# 3. BOUCLE SUR CHAQUE ENTREPRISE
for stock in stocks:
    name = stock["name"]
    ticker = stock["ticker"]
    
    print(f"Traitement de {name} ({ticker})...")
    
    # REQUÊTE FINANCIÈRE : On cible les termes d'analyse d'entreprise et de marché
    query_finance = f'("{name}" OR "{ticker}") AND (stock OR earnings OR quarterly OR revenue OR profit OR dividend OR inflation)'
    
    try:
        response = newsapi.get_everything(
            q=query_finance,
            language="en",
            sort_by="relevancy",       
            from_param=date_limite,    
            page_size=100              # On prend large pour filtrer sur les sources après
        )
        
        finbert_ready_data = {
            "ticker": ticker,
            "company_name": name,
            "date_filter": f"Last 7 days (since {date_limite})",
            "articles": []
        }
        
        for art in response["articles"]:
            if not art["title"] or not art["description"]:
                continue
            
            title_lower = art["title"].lower()
            source_lower = art["source"]["name"].lower()
            
            # FILTRE 1 : Le Nom ou le Ticker DOIT être explicitement dans le TITRE
            if name.lower() not in title_lower and ticker.lower() not in title_lower:
                continue
                
            # FILTRE 2 : Validation stricte de la source (L'article DOIT provenir d'un média financier de la liste)
            is_financial_media = any(media in source_lower for media in financial_sources)
            if not is_financial_media:
                continue  # Si la source n'est pas fiable/financière, on rejette l'article immédiatement
            
            # Stockage des informations
            finbert_ready_data["articles"].append({
                "source": art["source"]["name"],
                "date": art["publishedAt"],
                "title": art["title"],                          
                "summary": art["description"],                  
                "text_to_analyze": f"{art['title']}. {art['description']}"  
            })
            
            # Blocage strict à maximum 15 articles par entreprise
            if len(finbert_ready_data["articles"]) == 15:
                break
        
        # 4. SAUVEGARDE DANS LE DOSSIER 'NewsAPIàtraiter'
        output_file = output_dir / f"{ticker.lower()}_for_finbert.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(finbert_ready_data, f, ensure_ascii=False, indent=4)
            
        print(f"Fichier '{output_file.name}' généré avec {len(finbert_ready_data['articles'])} articles validés par les sources.\n")
        
    except Exception as e:
        print(f"Erreur lors de la récupération pour {name} : {e}\n")

print(f"Opération terminée ! Vos fichiers JSON contiennent uniquement des articles issus de sources financières validées.")