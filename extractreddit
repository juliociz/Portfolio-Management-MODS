import praw
import pandas as pd
import datetime

# 1. Authentification (Remplace par tes clés)
reddit = praw.Reddit(
    client_id="TON_CLIENT_ID",
    client_secret="TON_CLIENT_SECRET",
    user_agent="SentimentAnalysis_Project_v1.0 (by u/TonPseudo)"
)

def fetch_reddit_financial_data(subreddits=["wallstreetbets", "stocks", "investing"], limit=100):
    data = []
    
    for sub in subreddits:
        print(f"Scraping r/{sub}...")
        subreddit = reddit.subreddit(sub)
        
        # On récupère les posts les plus "chauds" (les plus discutés)
        for post in subreddit.hot(limit=limit):
            # Filtrer les posts épinglés (souvent des règles du forum)
            if not post.stickied:
                data.append({
                    "source": f"Reddit - r/{sub}",
                    "date": datetime.datetime.fromtimestamp(post.created_utc).isoformat(),
                    "title": post.title,
                    "text": post.selftext,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url
                })
                
    df = pd.DataFrame(data)
    # Nettoyage de base : on supprime les posts vides ou supprimés
    df = df[(df['text'] != '[deleted]') & (df['text'] != '[removed]')]
    
    # Sauvegarde locale
    df.to_csv("reddit_financial_data.csv", index=False)
    print(f"✅ {len(df)} posts récupérés avec succès.")
    return df

# Exécution
df_reddit = fetch_reddit_financial_data(limit=50)
