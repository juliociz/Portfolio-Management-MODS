import json
from newsapi import NewsApiClient

# 1. Connexion à l'API
NEWS_API_KEY = "f78933a29be64254b995b03134f70a7e"  # Mets ta vraie clé ici
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# 2. Paramètres de recherche (Médias financiers de premier plan)
TARGET_STOCK = "Tesla"
trusted_domains = "bloomberg.com,cnbc.com,reuters.com,wsj.com,ft.com"

print(f"🔄 Récupération et préparation des données pour FinBERT ({TARGET_STOCK})...")

response = newsapi.get_everything(
    q=TARGET_STOCK,
    domains=trusted_domains,
    language="en",
    sort_by="popularity",
    page_size=20
)

# 3. Structuration du JSON "Prêt pour le NLP"
finbert_ready_data = {
    "ticker": TARGET_STOCK,
    "data_format": "Merged Title and Description for NLP",
    "articles": []
}

for art in response["articles"]:
    if not art["title"] or not art["description"]:
        continue
    
    # 🌟 C'est cette clé 'text_to_analyze' que tu donneras directement à FinBERT
    full_text_signal = f"{art['title']}. {art['description']}"
    
    finbert_ready_data["articles"].append({
        "source": art["source"]["name"],
        "date": art["publishedAt"],
        "text_to_analyze": full_text_signal  # Texte dense, nettoyé et sans fioritures
    })

# 4. Sauvegarde
output_file = f"{TARGET_STOCK.lower()}_for_finbert.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(finbert_ready_data, f, ensure_ascii=False, indent=4)

print(f"✅ Fichier '{output_file}' généré et 100% prêt à être analysé !")