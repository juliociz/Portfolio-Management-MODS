import json
import os

INPUT_DIR = os.path.join(os.path.dirname(__file__), "AlphaVantageàtraiter")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "alphavantage_merged.json")

result = {}

for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".json"):
        continue

    filepath = os.path.join(INPUT_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    ticker = data["ticker"]
    texts = [article["text_to_analyze"] for article in data.get("articles", [])]
    result[ticker] = texts

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print(f"Fichier généré : {OUTPUT_FILE}")
for ticker, texts in result.items():
    print(f"  {ticker} : {len(texts)} articles")
