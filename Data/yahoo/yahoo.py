import os
import time
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup


def extract_full_text(url, headers):
    """Récupère le texte principal d'un article Yahoo Finance"""
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return ""

        soup = BeautifulSoup(r.text, "html.parser")

        # Yahoo Finance met souvent le contenu dans des <p>
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)

        return text.strip()

    except Exception:
        return ""


def fetch_yahoo_rss_news(tickers, output_csv):
    print(f"[Yahoo] Récupération RSS + contenu complet pour : {tickers}")
    all_news = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for ticker in tickers:
        print(f" -> Traitement {ticker}...")

        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                root = ET.fromstring(response.text)

                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""

                    try:
                        dt = parsedate_to_datetime(pub_date_str)
                    except:
                        dt = None

                    # 🔥 récupération du contenu complet
                    full_text = extract_full_text(link, headers)

                    all_news.append({
                        "ticker": ticker,
                        "date": dt,
                        "publisher": "Yahoo Finance",
                        "title": title,
                        "link": link,
                        "content": full_text
                    })

                    time.sleep(0.5)  # évite blocage

        except Exception as e:
            print(f"[Erreur] {ticker}: {e}")

        time.sleep(1)

    if all_news:
        df = pd.DataFrame(all_news)

        df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
        df = df.sort_values(by="date", ascending=False)

        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding="utf-8")

        print(f"\n[Succès] {len(df)} articles complets sauvegardés.")
        print(df[["ticker", "title"]].head(5))

    else:
        print("\n[Échec] Aucun article récupéré.")


if __name__ == "__main__":
    UNIVERS = ["NKE", "TGT", "DIS", "SBUX", "TSLA"]
    FILE_DESTINATION = "data_output/yahoo_news_full.csv"

    fetch_yahoo_rss_news(UNIVERS, FILE_DESTINATION)
    print("\n[Terminé] Extraction terminée.")