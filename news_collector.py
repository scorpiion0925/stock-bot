"""信頼できる経済ニュースRSSから取得"""
import feedparser

RSS_SOURCES = [
    ("ロイター", "https://assets.wor.jp/rss/rd/reuters/business.rss"),
    ("Yahoo経済", "https://news.yahoo.co.jp/rss/categories/business.xml"),
    ("東洋経済", "https://toyokeizai.net/list/feed/rss"),
]


def get_news(max_per_source=2):
    news_items = []
    for source_name, rss_url in RSS_SOURCES:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:max_per_source]:
                title = entry.title
                if len(title) > 70:
                    title = title[:67] + "..."
                news_items.append(f"[{source_name}] {title}")
        except Exception as e:
            print(f"RSS取得失敗 {source_name}: {e}")
    return news_items
