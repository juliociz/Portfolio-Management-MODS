# backtesting_2 — Backtest autonome PyPortfolioOpt

Ce dossier est une version autonome du backtesting MODS. Il ne dépend pas du reste du repository.

## Objectif

Tester une stratégie de portefeuille en poids continus :

```text
articles J-5 -> FinBERT -> sentiment_score
prix historiques -> momentum_score
sentiment + momentum -> global_score
global_score + prix historiques -> mu ajusté et covariance
PyPortfolioOpt -> poids continus optimisés
poids à J -> performance J à J+1
```

Il n'y a pas d'allocation discrète en nombre d'actions.

## Structure

```text
backtesting_2/
├── config_backtest.py
├── sentiment_backtest.py
├── prices_backtest.py
├── signals.py
├── risk_forecast.py
├── optimizer_pypfopt.py
├── engine_pypfopt.py
├── analyze_results.py
├── generate_test_data.py
├── data_input/
├── data_output/
└── results/
```

## Installation

Depuis la racine du repository :

```bash
source venv/bin/activate
pip install -r backtesting_2/requirements_backtesting.txt
```

## Données attendues

Mettre dans `backtesting_2/data_input/` un fichier par date de décision :

```text
alphavantage_merged_20260501.json
alphavantage_merged_20260504.json
...
```

Format attendu :

```json
{
  "TSLA": ["texte article 1", "texte article 2"],
  "NKE": ["texte article 1"],
  "DIS": [],
  "SBUX": [],
  "TGT": []
}
```

Chaque fichier du jour J doit contenir les articles J-5 déjà préparés.

## Test rapide avec données fictives

```bash
python -m backtesting_2.generate_test_data
python -m backtesting_2.engine_pypfopt
python -m backtesting_2.analyze_results
```

## Lancement avec données réelles

1. Placer les JSON AlphaVantage journaliers dans `backtesting_2/data_input/`.
2. Lancer :

```bash
python -m backtesting_2.engine_pypfopt
python -m backtesting_2.analyze_results
```

## Variante avec covariance ajustée par les signaux négatifs

```bash
python -m backtesting_2.engine_pypfopt --adjust-covariance
```

## Outputs

```text
backtesting_2/data_output/daily_sentiment_scores.csv
backtesting_2/data_output/daily_momentum_scores.csv
backtesting_2/data_output/daily_global_scores.csv
backtesting_2/data_output/daily_weights.csv

backtesting_2/results/portfolio_returns.csv
backtesting_2/results/weights_history.csv
backtesting_2/results/summary.json
backtesting_2/results/backtest_chart.png
```

## Logique anti look-ahead

Le moteur applique les poids calculés à la date J sur le rendement out-of-sample J -> J+1.

```text
signal disponible à J
-> poids optimisés à J
-> performance mesurée entre J et J+1
```

Cela évite d'utiliser une performance déjà réalisée pour décider du portefeuille.

## Git

À committer :
- les fichiers Python ;
- le README ;
- éventuellement les JSON de test si utiles.

À ne pas committer :
- `data_output/`
- `results/`
- gros fichiers de cache de prix si non nécessaires.
