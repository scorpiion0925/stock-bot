"""株探からPTS夜間ランキングを取得"""
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_kabutan_pts(url, max_rows=10):
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
            code = cols[0].get_text(strip=True) if cols[0] else ""
            name = cols[1].get_text(strip=True)
            change = cols[-2].get_text(strip=True) if len(cols) > 2 else ""
            change_pct = 0.0
            try:
                change_pct = float(change.replace('%', '').replace('+', '').replace(',', ''))
            except:
                pass
            results.append({"code": code, "name": name,
                            "change": change, "change_pct": change_pct})
        return results
    except Exception as e:
        print(f"PTS取得失敗: {e}")
        return []


def get_pts_ranking():
    return {
        "up": fetch_kabutan_pts("https://kabutan.jp/warning/?mode=4_3"),
        "down": fetch_kabutan_pts("https://kabutan.jp/warning/?mode=4_4"),
    }
