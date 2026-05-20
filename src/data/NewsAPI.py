import json
import os 
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Gestion du chemin du fichier .env
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 1. Connexion à l'API
NEWS_API_KEY = os.getenv("MY_NEWS_API_KEY")
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# 2. 🗓️ CALCUL DE LA DATE (Max 7 jours en arrière)
date_limite = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

TARGET_STOCK = "Tesla"

# 🌟 LA STRATÉGIE DE FILTRAGE : 
# On cherche "Tesla" obligatoirement lié au contexte boursier. 
# On supprime les domaines fermés pour laisser NewsAPI chercher sur tout son index financier de confiance.
query_finance = '(Tesla OR "TSLA") AND (stock OR earnings OR financial OR shares OR market)'

print(f"🔄 Récupération des 15 articles les plus importants depuis le {date_limite}...")

response = newsapi.get_everything(
    q=query_finance,
    language="en",
    sort_by="relevancy",       # Du plus pertinent au moins pertinent
    from_param=date_limite,    # 🌟 BLOCAGE STRICT À MAX 7 JOURS
    page_size=30               # On en demande 30 pour appliquer notre filtre anti-marques après
)

# 3. Structuration du JSON pour FinBERT
finbert_ready_data = {
    "ticker": TARGET_STOCK,
    "date_filter": f"Last 7 days (since {date_limite})",
    "articles": []
}

# Liste noire des mots polluants (Huawei, Hyundai, etc.)
blacklist = ["huawei", "hyundai", "toyota", "byd", "honda", "nissan", "review"]

for art in response["articles"]:
    if not art["title"] or not art["description"]:
        continue
    
    # Sécurité anti-pollution : on vérifie le titre et la description
    text_content = f"{art['title']} {art['description']}".lower()
    if any(bad_word in text_content for bad_word in blacklist):
        continue  # On ignore l'article s'il contient un concurrent
    
    full_text_signal = f"{art['title']}. {art['description']}"
    
    finbert_ready_data["articles"].append({
        "source": art["source"]["name"],
        "date": art["publishedAt"],
        "text_to_analyze": full_text_signal  
    })
    
    # 🌟 On s'arrête dès qu'on a atteint exactement 15 articles propres
    if len(finbert_ready_data["articles"]) == 15:
        break

# 4. Sauvegarde
output_dir = Path(__file__).resolve().parent
output_file = output_dir / f"{TARGET_STOCK.lower()}_for_finbert.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(finbert_ready_data, f, ensure_ascii=False, indent=4)

print(f"✅ Fichier '{output_file.name}' généré !")
print(f"📊 {len(finbert_ready_data['articles'])} articles 100% boursiers de moins de 7 jours prêts.")