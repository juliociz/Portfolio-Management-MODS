import json
import os
import re

# ============================================================
# Alignement précis avec ton arborescence (Dossier Mars)
# ============================================================

# 1. On trouve la racine du projet (le dossier parent de "Merge")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Chemin vers le dossier des données brutes de MARS 🛑
INPUT_DIR = os.path.join(BASE_DIR, "alphavantage_backtesting_mars2026")

# 3. Chemin pour le dossier de sortie (dans le dossier "Merge" à côté du script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "Merged_By_Day_Mars2026")

# Création du dossier de destination s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dictionnaire pour regrouper : { "YYYY-MM-DD": { "TICKER": [texts] } }
backtest_data_by_day = {}

print(f"📁 Recherche des fichiers bruts dans : {INPUT_DIR}")
print(f"📁 Sauvegarde des regroupements dans : {OUTPUT_DIR}\n")

if not os.path.exists(INPUT_DIR):
    print(f"❌ Erreur : Le dossier source '{INPUT_DIR}' n'a pas été trouvé.")
    print("Vérifie bien l'orthographe exacte du dossier (majuscules/minuscules ou tirets).")
    exit()

# os.walk scanne DIS, NKE, SBUX, TGT, TSLA...
for root, dirs, files in os.walk(INPUT_DIR):
    for filename in files:
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(root, filename)
        
        # Capture de la date YYYY-MM-DD
        match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        if not match:
            continue
            
        date_str = match.group(1)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            ticker = data.get("ticker")
            if not ticker:
                continue
                
            texts = [article["text_to_analyze"] for article in data.get("articles", [])]
            
            if date_str not in backtest_data_by_day:
                backtest_data_by_day[date_str] = {}
                
            backtest_data_by_day[date_str][ticker] = texts
            
        except Exception as e:
            print(f"⚠️ Impossible de lire le fichier {filename} : {e}")

if not backtest_data_by_day:
    print(f"❌ Aucun fichier JSON de ticker n'a pu être extrait.")
    exit()

print(f"\nÉcriture des fichiers quotidiens...")

# Génération des fichiers simplifiés quotidiens
for day, tickers_data in sorted(backtest_data_by_day.items()):
    output_file = os.path.join(OUTPUT_DIR, f"merged_{day}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tickers_data, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Généré : {os.path.basename(output_file)}")
    for ticker, texts in tickers_data.items():
        print(f"  └─ {ticker} : {len(texts)} articles")

print("\nFusion terminée avec succès ! 🚀")