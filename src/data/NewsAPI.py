import json
from newsapi import NewsApiClient

# 1. Connexion
NEWS_API_KEY = "f78933a29be64254b995b03134f70a7e"  # Mets ta vraie clé
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# 2. Ta liste de médias de confiance (Wall Street Standard)
trusted_domains = "bloomberg.com,cnbc.com,reuters.com,wsj.com,ft.com"

# 3. Requête ciblée (On cherche juste l'action dans ces médias précis)
TARGET_STOCK = "Tesla"

response = newsapi.get_everything(
    q=TARGET_STOCK,
    domains=trusted_domains,  # 🌟 LA MAGIE EST ICI : l'API ignore le reste du web
    language="en",
    sort_by="publishedAt",    # 'publishedAt' pour avoir les toutes dernières news, ou 'popularity'
    page_size=15
)

# 4. Structuration du JSON propre
cleaned_data = {
    "ticker": TARGET_STOCK,
    "filter": "Top Financial Media Only",
    "articles": []
}

for art in response["articles"]:
    if not art["title"] or not art["description"]:
        continue
        
    cleaned_data["articles"].append({
        "source": art["source"]["name"],  # Tu verras s'afficher "Bloomberg", "Reuters"...
        "date": art["publishedAt"],
        "title": art["title"],
        "description": art["description"],
        "url": art["url"]
    })

# 5. Sauvegarde
with open(f"{TARGET_STOCK.lower()}_premium_news.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

print(f"Fichier premium créé ! {len(cleaned_data['articles'])} articles récupérés sur les médias du Top Tier.")