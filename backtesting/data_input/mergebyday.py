import json
import os
import re

# Configuré exactement selon ton arborescence
INPUT_DIR = os.path.join(os.path.dirname(__file__), "AlphaVantage_Backtest")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "Merged_By_Day")

# Création du dossier de destination
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dictionnaire pour regrouper : { "YYYY-MM-DD": { "TICKER": [texts] } }
backtest_data_by_day = {}

print(f"Démarrage du scan dans : {INPUT_DIR}\n")

# os.walk va descendre automatiquement dans les sous-dossiers DIS, NKE, etc.
for root, dirs, files in os.walk(INPUT_DIR):
    for filename in files:
        # On vérifie que c'est bien un fichier JSON
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(root, filename)
        
        # Capture de la date YYYY-MM-DD (ex: dis_2025-05-11.json)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        if not match:
            continue
            
        date_str = match.group(1) # Donne "2025-05-11"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extraction sécurisée du ticker et des textes
            ticker = data.get("ticker")
            if not ticker:
                continue
                
            texts = [article["text_to_analyze"] for article in data.get("articles", [])]
            
            # Initialisation de la journée si elle n'existe pas encore
            if date_str not in backtest_data_by_day:
                backtest_data_by_day[date_str] = {}
                
            # On stocke les textes dans la case du jour et du ticker correspondant
            backtest_data_by_day[date_str][ticker] = texts
            
        except Exception as e:
            print(f"⚠️ Impossible de lire le fichier {filename} : {e}")

print(f"\nÉcriture des fichiers regroupés dans '{OUTPUT_DIR}'...")

# Génération des fichiers simplifiés quotidiens
for day, tickers_data in sorted(backtest_data_by_day.items()):
    output_file = os.path.join(OUTPUT_DIR, f"merged_{day}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tickers_data, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Fichier généré pour le {day} : {os.path.basename(output_file)}")
    for ticker, texts in tickers_data.items():
        print(f"  └─ {ticker} : {len(texts)} articles")

print("\nFélicitations, tous tes fichiers de backtest sont fusionnés par journée !")