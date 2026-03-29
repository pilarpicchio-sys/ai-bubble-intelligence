def analyze_news():
    import feedparser
    from textblob import TextBlob

    RSS_FEEDS = [
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://www.ilsole24ore.com/rss/tecnologia.xml"
    ]

    KEYWORDS = ["AI", "artificial intelligence", "OpenAI", "Anthropic", "machine learning"]

    headlines = []
    sentiment_scores = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:5]:
                title = entry.title.strip()

                # 🔥 FILTRO QUI (punto giusto)
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    headlines.append(title)
                    sentiment_scores.append(TextBlob(title).sentiment.polarity)

        except Exception as e:
            headlines.append(f"Errore feed: {str(e)}")
            sentiment_scores.append(0)

    # fallback
    if not headlines:
        headlines = ["Nessuna notizia AI rilevante trovata"]
        sentiment_scores = [0]

    # calcolo sentiment medio
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    # numero news
    news_volume = len(headlines)

    # ✅ QUESTA RIGA DEVE STARE DENTRO
    return headlines, avg_sentiment, news_volume