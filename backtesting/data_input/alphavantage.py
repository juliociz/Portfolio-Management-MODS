import json
from pathlib import Path
from datetime import timedelta

import requests


def get_finbert_ready_news(
    ticker,
    company_name,
    target_date,
    api_key,
    output_dir,
    relevance_threshold=0.35,
    max_articles=50
):
    """
    Exemple :

    target_date = 2025-05-01

    => récupération des articles du
       2025-04-24 au 2025-04-30 inclus
    """

    date_start = target_date - timedelta(days=7)
    date_end = target_date - timedelta(days=1)

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "time_from": date_start.strftime("%Y%m%dT0000"),
        "time_to": date_end.strftime("%Y%m%dT2359"),
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
        f"{date_start.date()} -> {date_end.date()} | "
        f"{len(articles_bruts)} articles bruts"
    )

    finbert_ready_data = {
        "ticker": ticker,
        "company_name": company_name,
        "target_date": target_date.strftime("%Y-%m-%d"),
        "window_start": date_start.strftime("%Y-%m-%d"),
        "window_end": date_end.strftime("%Y-%m-%d"),
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

        has_name = company_lower in text_combined

        has_ticker = (
            f" {ticker_lower} " in f" {text_combined} "
            or f"({ticker_lower})" in text_combined
            or f"{ticker_lower}:" in text_combined
        )

        if not has_name and not has_ticker:
            continue

        ticker_relevance = 0.0

        for ticker_info in item.get("ticker_sentiment", []):

            if ticker_info["ticker"] == ticker:
                ticker_relevance = float(
                    ticker_info["relevance_score"]
                )
                break

        if ticker_relevance < relevance_threshold:
            continue

        finbert_ready_data["articles"].append({
            "source": item.get("source"),
            "date": item.get("time_published"),
            "title": title,
            "summary": summary,
            "text_to_analyze": f"{title}. {summary}",
            "alpha_vantage_sentiment_label":
                item.get("overall_sentiment_label"),
            "ticker_relevance_score":
                ticker_relevance
        })

        if len(finbert_ready_data["articles"]) >= max_articles:
            break

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{ticker.lower()}_"
        f"{date_end.strftime('%Y-%m-%d')}.json"
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