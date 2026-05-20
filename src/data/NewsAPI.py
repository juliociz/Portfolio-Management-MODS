import json
from newsapi import NewsApiClient

# 1. Configuration
NEWS_API_KEY = "f78933a29be64254b995b03134f70a7e"  # Mets ta clé ici
TARGET_STOCK = "Tesla"

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# 2. Construction de la requête multi-sources
# On cible l'entreprise ET des mots-clés qui forcent le contenu financier/business
query = f"{TARGET_STOCK} AND (stock OR shares OR earnings OR revenue OR business OR market)"

# Optionnel : Tu peux lister des domaines précis si tu veux filtrer au maximum
# exemples : bloomberg.com, cnbc.com, reuters.com, wsj.com
# Pour ce script, on reste sur 'popularity' qui remonte naturellement ces grands médias.

print(f"Recherche d'informations globales sur {TARGET_STOCK}...")

# 3. Appel à l'API
response = newsapi.get_everything(
    q=query,
    language="en",
    sort_by="popularity",  # Trie par l'importance du média (Bloomberg, CNBC passeront devant)
    page_size=30           # On récupère les 30 articles les plus importants
)

# 4. Nettoyage et structuration des données pour ton projet
# Au lieu de garder tout le jargon technique de l'API, on extrait un JSON super propre
cleaned_data = {
    "ticker": TARGET_STOCK,
    "total_articles_found": len(response["articles"]),
    "articles": []
}

for art in response["articles"]:
    # On ignore les articles sans titre ou sans description
    if not art["title"] or not art["description"]:
        continue
        
    article_info = {
        "source_media": art["source"]["name"],        # Ex: "Bloomberg", "CNBC"
        "date_publication": art["publishedAt"],       # Date et heure
        "title": art["title"],                        # Le titre de la news
        "description": art["description"],            # Le résumé de la news
        "url": art["url"]                             # Lien vers l'article complet
    }
    cleaned_data["articles"].append(article_info)

# 5. Sauvegarde dans le fichier JSON
filename = f"{TARGET_STOCK.lower()}_multi_source_news.json"
with open(filename, "w", encoding="utf-8") as fichier:
    json.dump(cleaned_data, fichier, ensure_ascii=False, indent=4)

print(f"Succès ! Le fichier '{filename}' a été créé avec {len(cleaned_data['articles'])} articles financiers qualitatifs.")