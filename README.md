# Portfolio Management MODS

Projet académique de gestion automatisée de portefeuille intégrant des signaux de **sentiment** (NLP via FinBERT) et de **momentum** pour optimiser les allocations d'actifs.

---

## Objectif

Étudier si l'intégration de données sentimentales (news financières) peut améliorer les performances d'un portefeuille d'actions du S&P 500.

---

## Architecture du projet

```
Portfolio-Management-MODS/
│
├── src/
│   ├── data/
│   │   ├── fetch_prices.py      # Prix historiques (Yahoo Finance)
│   │   └── fetch_news.py        # Articles financiers (NewsAPI)
│   ├── sentiment/
│   │   └── finbert.py           # Analyse de sentiment (FinBERT)
│   ├── momentum/
│   │   └── momentum.py          # Indicateur de momentum
│   └── portfolio/
│       ├── scorer.py            # Score global sentiment + momentum
│       └── optimizer.py         # Optimisation (PyPortfolioOpt / Black-Litterman)
│
├── backtesting/
│   └── backtest.py              # Évaluation de la stratégie
│
├── notebooks/                   # Exploration et prototypage
├── tests/                       # Tests unitaires
├── data/                        # Données (gitignorées)
├── config.py                    # Paramètres globaux
├── main.py                      # Pipeline principal
└── requirements.txt
```

---

## Répartition des tâches

| Module | Responsable | Branche Git |
|--------|------------|-------------|
| `src/data/fetch_prices.py` | À assigner | `feature/fetch-prices` |
| `src/data/fetch_news.py` | À assigner | `feature/fetch-news` |
| `src/sentiment/finbert.py` | À assigner | `feature/sentiment-finbert` |
| `src/momentum/momentum.py` | À assigner | `feature/momentum` |
| `src/portfolio/optimizer.py` | À assigner | `feature/portfolio-optim` |
| `backtesting/backtest.py` | À assigner | `feature/backtesting` |

---

## Installation

### 1. Cloner le repo

```bash
git clone https://github.com/juliociz/Portfolio-Management-MODS.git
cd Portfolio-Management-MODS
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les clés API

```bash
cp .env.example .env
# Éditer .env et renseigner NEWS_API_KEY
```

---

## Utilisation

```bash
# Pipeline complet V1 (Sentiment + Momentum)
python main.py --version v1

# Pipeline complet V2 (+ Black-Litterman)
python main.py --version v2

# Télécharger les données uniquement
python main.py --fetch-only

# Utiliser les données locales (sans refetch)
python main.py --version v1 --no-fetch
```

---

## Tests

```bash
pytest tests/
```

---

## Stack technique

| Outil | Usage |
|-------|-------|
| `yfinance` | Prix historiques |
| `newsapi-python` | Articles financiers |
| `ProsusAI/finbert` | Analyse de sentiment NLP |
| `PyPortfolioOpt` | Optimisation de portefeuille |
| `bt` | Backtesting |

---

## Versions

### V1 — Sentiment + Momentum
- Récupération des prix et des news
- Score de sentiment via FinBERT
- Score de momentum multi-fenêtres (1m, 3m, 6m)
- Score global → poids du portefeuille
- Backtesting vs S&P 500

### V2 — Black-Litterman
- Les scores sentiment+momentum deviennent des **vues** dans le modèle Black-Litterman
- Optimisation sous contraintes de risque
- Comparaison V1 vs V2

---

## Équipe

Jules, Blaise, Etienne, Hugo — Projet MODS
