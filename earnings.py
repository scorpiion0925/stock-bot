"""超絶決算情報の取得（サプライズ重視で抽出）"""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

PREMIUM_KEYWORDS = {
    "最高益": 25, "上方修正": 30, "サプライズ": 20, "倍増": 25,
    "急増益": 20, "自社株買い": 18, "増配": 15, "記念配当": 12,
    "特別配当": 12, "株式分割": 15, "業績予想": 10, "復配": 18,
    "連続最高": 22, "黒字転換": 28,
}


def fetch_kabutan_news(url, max_items=30):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        items = []
        for li in soup.find_all(["li", "tr"])[:max_items * 2]:
            text = li.get_text(strip=True)
            if len(text) < 10 or len(text) > 200:
                continue
            code_match = re.search(r'\b([0-9]{4})\b', text)
            code = code_match.group(1) if code_match else ""
            items.append({"headline": text[:120], "code": code})
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        print(f"決算ニュース取得失敗: {e}")
        return []


def score_earnings(headline):
    score = 0
    matched = []
    for kw, weight in PREMIUM_KEYWORDS.items():
        if kw in headline:
            score += weight
            matched.append(kw)
    m = re.search(r'([0-9.]+)倍', headline)
    if m:
        try:
            mult = float(m.group(1))
            if mult >= 2:
                score += min(int(mult * 5), 30)
        except:
            pass
    pm = re.search(r'([+-])([0-9.]+)[％%]', headline)
    if pm and pm.group(1) == '+':
        try:
            score += min(int(float(pm.group(2)) / 3), 20)
        except:
            pass
    return score, matched


def get_premium_earnings():
    urls = [
        "https://kabutan.jp/news/marketnews/?category=8",
        "https://kabutan.jp/news/marketnews/?category=15",
    ]
    all_items = []
    for url in urls:
        all_items.extend(fetch_kabutan_news(url))

    scored = []
    seen = set()
    for item in all_items:
        if item['headline'] in seen:
            continue
        seen.add(item['headline'])
        score, matched = score_earnings(item['headline'])
        if score >= 15:
            scored.append({"headline": item['headline'], "code": item['code'],
                          "score": score, "matched": matched})
    scored.sort(key=lambda x: -x['score'])
    return {"top": scored[:10]}
