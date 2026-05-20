# 📈 Suivi d'Avancement du Projet - Portfolio Management

Ce fichier centralise l'avancement de l'équipe. **À mettre à jour à chaque fin de session** avant de faire un `git push`. 
Pour cocher une case, remplacez `[ ]` par `[x]`.

---

## 👥 Répartition des Rôles & Tâches

### 1. Data Ingestion (Récupération des Données)
* **Responsable :** @NomCollegue1
* [x] Script d'extraction des prix historiques (Yahoo Finance) `src/data/fetch_prices.py`
* [x] Script d'extraction des actualités épurées (NewsAPI) `src/data/get_news.py`
* [ ] Automatisation du pipeline de données dans `main.py`
* *Notes/Bloquants :* Le script NewsAPI est calibré sur les 7 derniers jours pour éviter le bruit.

### 2. Sentiment Analysis (NLP / FinBERT)
* **Responsable :** @NomCollegue2
* [ ] Configuration de FinBERT et chargement du modèle `src/sentiment/finbert.py`
* [ ] Traitement du JSON généré par NewsAPI (`text_to_analyze`)
* [ ] Extraction des scores de sentiment (-1 à 1) par article
* *Notes/Bloquants :* En attente du format JSON final (Validé, prêt à coder).

### 3. Momentum & Scorer
* **Responsable :** @NomCollegue3
* [ ] Calcul des indicateurs de Momentum `src/momentum/momentum.py`
* [ ] Création de la matrice de scoring combinée (Sentiment + Momentum) `src/portfolio/scorer.py`
* *Notes/Bloquants :* Pas de problème technique pour le moment.

### 4. Optimization & Backtesting (Black-Litterman)
* **Responsable :** @NomCollegue4
* [ ] Modélisation de la stratégie avec PyPortfolioOpt `src/portfolio/optimizer.py`
* [ ] Intégration des vues du modèle basées sur le Scorer boursier
* [ ] Code de backtesting de la stratégie `backtesting/backtest.py`
* *Notes/Bloquants :* Besoin des scores de sentiment pour affiner les vues de Black-Litterman.

---

## 📅 Journal des Mises à Jour (Historique Récent)

*Laissez un mot rapide ici à chaque fois que vous poussez une modification importante.*

* **20 Mai 2026 (@ton_pseudo) :** Mise en place du script `get_news.py` avec filtrage strict par ticker boursier, blocage à J-7 et exclusion automatique des concurrents automobiles (Huawei, Hyundai...). Stockage sécurisé de la clé API dans le `.env` et configuration du `.gitignore`.
* **[Date] (@Auteur) :** [Ce qui a été fait ou ce qui bloque]
* **[Date] (@Auteur) :** [Ce qui a été fait ou ce qui bloque]