import json
import os
import re

# ============================================================
# Configuration des dossiers pour Avril 2026
# ============================================================
# Le script pointe maintenant sur ton nouveau dossier source
INPUT_DIR = os.path.join(os.path.dirname(__file__), "alphavantage_backtesting_avril2026")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "Merged_By_Day_Avril2026")

# Création du dossier de destination s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dictionnaire pour regrouper : { "YYYY-MM-DD": { "TICKER": [texts] } }
backtest_data_by_day = {}

print(f"📁 Dossier source détecté : {INPUT_DIR}")
print(f"📁 Dossier de sortie configuré : {OUTPUT_DIR}")
print("Démarrage du scan des fichiers JSON...\n")

# os.walk descend automatiquement dans alphavantage_backtesting_avril2026/DIS, /NKE, etc.
for root, dirs, files in os.walk(INPUT_DIR):
    # Sécurité pour éviter de relire le dossier de sortie s'il est au même endroit
    if "Merged_By_Day_Avril2026" in root:
        continue
        
    for filename in files:
        # On ne traite que les fichiers JSON
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(root, filename)
        
        # Capture de la date YYYY-MM-DD (ex: dis_2026-04-15.json)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        if not match:
            continue
            
        date_str = match.group(1)  # Extrait proprement "2026-04-15"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extraction du ticker et des textes à analyser
            ticker = data.get("ticker")
            if not ticker:
                continue
                
            texts = [article["text_to_analyze"] for article in data.get("articles", [])]
            
            # Initialisation de la journée dans notre dictionnaire si besoin
            if date_str not in backtest_data_by_day:
                backtest_data_by_day[date_str] = {}
                
            # On ajoute les textes trouvés pour ce ticker à cette date précise
            backtest_data_by_day[date_str][ticker] = texts
            
        except Exception as e:
            print(f"⚠️ Impossible de lire le fichier {filename} : {e}")

if not backtest_data_by_day:
    print(f"❌ Aucun fichier JSON valide n'a été trouvé dans '{INPUT_DIR}'.")
    print("Vérifie que le dossier contient bien tes sous-dossiers de tickers.")
    exit()

print(f"\nÉcriture des fichiers regroupés par jour dans '{OUTPUT_DIR}'...")

# Génération des fichiers simplifiés quotidiens (ex: merged_2026-04-15.json)
for day, tickers_data in sorted(backtest_data_by_day.items()):
    output_file = os.path.join(OUTPUT_DIR, f"merged_{day}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tickers_data, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Fichier généré pour le {day} : {os.path.basename(output_file)}")
    for ticker, texts in tickers_data.items():
        print(f"  └─ {ticker} : {len(texts)} articles")

print("\nFélicitations, la fusion des données d'Avril 2026 est terminée ! 🚀")