"""引け前用：当日の市場状況を取得"""
import requests
from bs4 import BeautifulSoup
import yfinance as yf

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fmt(value, suffix=""):
    return f"{value:,.2f}{suffix}" if value is not None else "N/A"


def fmt_change(price, prev):
    if price is None or prev is None:
        return ""
    change = price - prev
    pct = (change / prev) * 100
    sign = "+" if change >= 0 else ""
    return f" ({sign}{change:,.2f} / {sign}{pct:.2f}%)"


def get_intraday_summary():
    def get(sym):
        try:
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            if len(h) < 1:
                return None, None
            return h['Close'].iloc[-1], (h['Close'].iloc[-2] if len(h) >= 2 else None)
        except:
            return None, None

    nikkei, n_prev = get("^N225")
    topix, t_prev = get("1306.T")
    mothers, m_prev = get("2516.T")
    usdjpy, _ = get("JPY=X")
    wti, _ = get("CL=F")

    return {
        "nikkei": fmt(nikkei, "円") + fmt_change(nikkei, n_prev),
        "topix": fmt(topix) + fmt_change(topix, t_prev),
        "mothers": fmt(mothers) + fmt_change(mothers, m_prev),
        "usdjpy": fmt(usdjpy, "円"),
        "wti": fmt(wti, "ドル"),
    }


def fetch_kabutan_ranking(url, max_rows=10):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding if res.apparent_encoding else "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        table = soup.find("table", class_="stock_table")
        if not table:
            return []
        for row in table.find_all("tr")[1:max_rows + 1]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            name = cols[1].get_text(strip=True)
            change = cols[-2].get_text(strip=True) if len(cols) > 2 else ""
            results.append({"name": name, "change": change})
        return results
    except Exception as e:
        print(f"取得失敗: {e}")
        return []


def get_intraday_rankings():
    return {
        "up": fetch_kabutan_ranking("https://kabutan.jp/warning/?mode=2_1"),
        "down": fetch_kabutan_ranking("https://kabutan.jp/warning/?mode=2_2"),
        "volume": fetch_kabutan_ranking("https://kabutan.jp/warning/?mode=3_1"),
    }
