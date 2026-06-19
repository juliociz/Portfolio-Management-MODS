# Backtesting V1 — Sentiment + Momentum

Ce dossier contient une structure de backtesting séparée du pipeline principal.

## Objectif

Simuler une stratégie sur mai 2026 :

1. Chaque jour `J`, charger `alphavantage_merged_YYYYMMDD.json`.
2. Calculer le sentiment FinBERT sur les articles fournis pour ce jour.
3. Calculer le momentum avec les prix historiques disponibles jusqu'à `J`.
4. Fusionner sentiment + momentum en score global.
5. Transformer les scores en poids cibles.
6. Simuler les transactions depuis le portefeuille de la veille.
7. Exporter l'historique, les transactions et le résumé.

## Structure attendue

```text
backtesting/
├── config_backtest.py
├── sentiment_backtest.py
├── prices_backtest.py
├── signal_backtest.py
├── allocator_backtest.py
├── engine.py
├── analyze_results.py
├── generate_test_data.py
├── data_input/
├── data_output/
└── results/
```

## Format des inputs

Dans `backtesting/data_input/`, ajouter les fichiers :

```text
alphavantage_merged_20260501.json
alphavantage_merged_20260504.json
...
```

Format JSON attendu :

```json
{
  "TSLA": ["article 1", "article 2"],
  "NKE": ["article 1", "article 2"],
  "TGT": ["article 1", "article 2"],
  "DIS": ["article 1", "article 2"],
  "SBUX": ["article 1", "article 2"]
}
```

## Lancer un test rapide avec données fictives

Depuis la racine du projet :

```bash
source venv/bin/activate
python -m backtesting.generate_test_data
python -m backtesting.engine
python -m backtesting.analyze_results
```

## Lancer avec les vraies données

Mettre les vrais fichiers JSON dans :

```text
backtesting/data_input/
```

Puis :

```bash
python -m backtesting.engine
python -m backtesting.analyze_results
```

## Outputs

```text
backtesting/results/portfolio_history.csv
backtesting/results/transactions_log.csv
backtesting/results/summary.json
backtesting/results/portfolio_value.png
backtesting/results/realized_weights.png

backtesting/data_output/daily_sentiment_scores.csv
backtesting/data_output/daily_momentum_scores.csv
backtesting/data_output/daily_target_weights.csv
```

## Convention V1

- Pas de frais de transaction.
- Pas de slippage.
- Actions entières.
- Rééquilibrage quotidien uniquement lorsque le fichier JSON journalier existe.
- Prix d'exécution : dernier prix de clôture disponible à la date `J`.
