"""
ゴールデンクロス銘柄の抽出（両方併用）
1. 株探のGCランキングをスクレイピング
2. 主要銘柄をyfinanceで自前計算
"""
import requests
from bs4 import BeautifulSoup
from technical import analyze_ticker, format_tech_summary

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

MAJOR_TICKERS = [
    ("トヨタ", "7203.T"), ("ソニーG", "6758.T"), ("キーエンス", "6861.T"),
    ("三菱UFJ", "8306.T"), ("ファストリ", "9983.T"), ("ソフトバンクG", "9984.T"),
    ("東エレク", "8035.T"), ("信越化学", "4063.T"), ("日立", "6501.T"),
    ("三菱商事", "8058.T"), ("リクルート", "6098.T"), ("KDDI", "9433.T"),
    ("デンソー", "6902.T"), ("村田製作所", "6981.T"), ("ファナック", "6954.T"),
    ("HOYA", "7741.T"), ("任天堂", "7974.T"), ("ダイキン", "6367.T"),
    ("アドテスト", "6857.T"), ("第一三共", "4568.T"),
]


def scrape_kabutan_golden_cross():
    url = "https://kabutan.jp/warning/?mode=6_1"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        table = soup.find("table", class_="stock_table")
        if not table:
            return []
        for row in table.find_all("tr")[1:21]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            # 列構造: [0]コード [1]市場区分 [2]会社名 [3]株価 ...
            code = cols[0].get_text(strip=True)
            name = cols[2].get_text(strip=True) if len(cols) > 2 else cols[1].get_text(strip=True)
            price = cols[3].get_text(strip=True) if len(cols) > 3 else ""
            results.append({"code": code, "name": name, "price": price,
                           "type": "5×25", "source": "株探", "tech": ""})
        return results
    except Exception as e:
        print(f"株探GC取得失敗: {e}")
        return []


def compute_major_golden_cross():
    results = []
    for name, sym in MAJOR_TICKERS:
        analysis = analyze_ticker(sym)
        if analysis is None:
            continue
        tech = format_tech_summary(analysis)
        price = analysis["latest"]["price"]
        if analysis["gc_5_25"]:
            results.append({"code": sym.replace(".T", ""), "name": name,
                           "price": f"{price:,.0f}円", "type": "5×25",
                           "source": "自前計算", "tech": tech})
        elif analysis["gc_25_75"]:
            results.append({"code": sym.replace(".T", ""), "name": name,
                           "price": f"{price:,.0f}円", "type": "25×75",
                           "source": "自前計算", "tech": tech})
    return results


def get_golden_cross_stocks():
    kabutan = scrape_kabutan_golden_cross()
    major = compute_major_golden_cross()
    merged = {}
    for item in kabutan:
        merged[item["code"]] = item
    for item in major:
        merged[item["code"]] = item
    all_gc = list(merged.values())
    short_gc = [x for x in all_gc if x["type"] == "5×25"]
    mid_gc = [x for x in all_gc if x["type"] == "25×75"]
    return {"short": short_gc[:15], "mid": mid_gc[:10]}
