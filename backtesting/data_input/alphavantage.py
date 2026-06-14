import json
import os
import re
import pytz
import requests
from datetime import datetime, timedelta
from pathlib import Path

def get_finbert_ready_news(
    ticker,
    company_name,
    target_date,  # On s'attend à un objet datetime
    api_key,
    output_dir,
    relevance_threshold=0.35,
    max_articles=50
):
    """
    Récupère les articles financiers pour un ticker donné selon les horaires de la bourse US (NYSE/NASDAQ).
    Fenêtre cible : de la dernière fermeture (16h00) à 3 minutes avant l'ouverture du jour (09h27).
    """
    # 1. Gestion stricte des fuseaux horaires (New York)
    tz_ny = pytz.timezone("America/New_York")
    
    # Sécurité si target_date arrive sous forme de simple 'date', on convertit
    if not isinstance(target_date, datetime):
        target_datetime = datetime.combine(target_date, datetime.min.time())
    else:
        target_datetime = target_date

    # On localise la date cible à minuit, heure de New York
    target_datetime = tz_ny.localize(target_datetime.replace(hour=0, minute=0, second=0, microsecond=0))

    # Borne de FIN : 9h27 le jour même (3 min avant l'ouverture de la bourse)
    date_end = target_datetime.replace(hour=9, minute=27)

    # Borne de DÉBUT : 16h00 la veille (fermeture de la bourse précédente)
    if target_datetime.weekday() == 0:  # 0 = Lundi
        # Si on est lundi, la dernière fermeture remonte au vendredi précédent
        date_start = (target_datetime - timedelta(days=3)).replace(hour=16, minute=0)
    else:
        # Sinon, c'est simplement la veille
        date_start = (target_datetime - timedelta(days=1)).replace(hour=16, minute=0)

    # Formatage des dates requis par l'API Alpha Vantage (YYYYMMDDTHHMM)
    time_from_str = date_start.strftime("%Y%m%dT%H%M")
    time_to_str = date_end.strftime("%Y%m%dT%H%M")

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "time_from": time_from_str,
        "time_to": time_to_str,
        "sort": "LATEST",
        "limit": 1000,
        "apikey": api_key
    }

    response = requests.get(
        "https://www.alphavantage.co/query",
        params=params,
        timeout=30
    )

    data = response.json()

    if "feed" not in data:
        raise Exception(
            f"Erreur Alpha Vantage : "
            f"{data.get('Information', 'Erreur inconnue')}"
        )

    articles_bruts = data.get("feed", [])

    print(
        f"{ticker} | "
        f"Fenêtre US ({date_start.strftime('%d/%m %H:%M')} -> {date_end.strftime('%d/%m %H:%M')}) | "
        f"{len(articles_bruts)} articles bruts"
    )

    finbert_ready_data = {
        "ticker": ticker,
        "company_name": company_name,
        "target_date": target_datetime.strftime("%Y-%m-%d"),
        "window_start": date_start.strftime("%Y-%m-%d %H:%M"),
        "window_end": date_end.strftime("%Y-%m-%d %H:%M"),
        "articles": []
    }

    for item in articles_bruts:
        title = item.get("title")
        summary = item.get("summary")

        if not title or not summary:
            continue

        text_combined = f"{title} {summary}".lower()
        company_lower = company_name.lower()
        ticker_lower = ticker.lower()

        # Double sécurité textuelle
        has_name = company_lower in text_combined
        
        # 🛑 RECTIFICATION REGEX : Évite les collisions (ex: "nke" dans "brand engagement")
        has_ticker = bool(re.search(r"\b" + re.escape(ticker_lower) + r"\b", text_combined))

        if not has_name and not has_ticker:
            continue

        ticker_relevance = 0.0
        for ticker_info in item.get("ticker_sentiment", []):
            if ticker_info["ticker"] == ticker:
                ticker_relevance = float(ticker_info["relevance_score"])
                break

        if ticker_relevance < relevance_threshold:
            continue

        finbert_ready_data["articles"].append({
            "source": item.get("source"),
            "date": item.get("time_published"),
            "title": title,
            "summary": summary,
            "text_to_analyze": f"{title}. {summary}",
            "alpha_vantage_sentiment_label": item.get("overall_sentiment_label"),
            "ticker_relevance_score": ticker_relevance
        })

        if len(finbert_ready_data["articles"]) >= max_articles:
            break

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarde avec la date cible pour le backtest
    filename = (
        f"{ticker.lower()}_"
        f"{target_datetime.strftime('%Y-%m-%d')}.json"
    )

    output_file = output_dir / filename

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            finbert_ready_data,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"✔ {filename} sauvegardé "
        f"({len(finbert_ready_data['articles'])} articles)"
    )

    return finbert_ready_data