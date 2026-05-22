"""
株式情報Webページ生成 - メイン（全機能搭載版）
朝・引け前どちらの時間でも動作し、index.htmlを生成する。
"""
from datetime import datetime
import pytz

from market_data import get_market_summary
from pts_scraper import get_pts_ranking
from earnings import get_premium_earnings
from screener import get_top5_attention
from intraday_data import get_intraday_summary, get_intraday_rankings
from news_collector import get_news
from golden_cross import get_golden_cross_stocks


def main():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    date_str = now.strftime('%Y/%m/%d (%a) %H:%M')
    is_morning = now.hour < 10

    print(f"=== ページ生成 {date_str} (morning={is_morning}) ===")

    market = get_market_summary()
    pts = get_pts_ranking()
    earnings = get_premium_earnings()
    top5 = get_top5_attention(pts, earnings)
    news = get_news()

    print("ゴールデンクロス銘柄を抽出中...")
    golden = get_golden_cross_stocks()

    intraday = None
    rankings = None
    if not is_morning:
        intraday = get_intraday_summary()
        rankings = get_intraday_rankings()

    html = build_html(date_str, is_morning, market, pts, earnings,
                      top5, news, intraday, rankings, golden)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html を生成しました")


def build_html(date_str, is_morning, market, pts, earnings,
               top5, news, intraday, rankings, golden):
    mode_label = "🌅 朝のレポート" if is_morning else "📊 引け前レポート"

    top5_html = ""
    for i, item in enumerate(top5, 1):
        top5_html += f'''
        <div class="rank-item">
          <span class="rank-num">{i}位</span>
          <span class="rank-name">{item['name']}</span>
          <span class="rank-score">スコア {item['score']:.1f}</span>
          <div class="rank-reason">{item['reason']}</div>
        </div>'''
    if not top5_html:
        top5_html = '<p class="empty">データ取得待ち（平日朝に更新）</p>'

    def gc_block(items):
        if not items:
            return '<p class="empty">該当なし</p>'
        h = ""
        for x in items:
            tech = f'<div class="rank-reason">{x["tech"]}</div>' if x.get("tech") else ""
            h += f'''
            <div class="gc-item">
              <span class="gc-name">{x["name"]}({x["code"]})</span>
              <span class="gc-price">{x["price"]}</span>
              <span class="gc-src">{x["source"]}</span>
              {tech}
            </div>'''
        return h

    gc_short_html = gc_block(golden.get("short", []))
    gc_mid_html = gc_block(golden.get("mid", []))

    earnings_html = ""
    for e in earnings.get('top', [])[:8]:
        earnings_html += f'<li>{e["headline"]}</li>'
    if not earnings_html:
        earnings_html = '<li class="empty">データ取得待ち</li>'

    adr_html = ""
    for adr in market['adrs']:
        adr_html += f'<tr><td>{adr["name"]}</td><td>{adr["change"]}</td></tr>'

    pts_up_html = ""
    for i, item in enumerate(pts.get('up', [])[:5], 1):
        pts_up_html += f'<tr><td>{i}</td><td>{item["name"]}</td><td>{item["change"]}</td></tr>'
    pts_down_html = ""
    for i, item in enumerate(pts.get('down', [])[:5], 1):
        pts_down_html += f'<tr><td>{i}</td><td>{item["name"]}</td><td>{item["change"]}</td></tr>'

    news_html = ""
    for n in news[:6]:
        news_html += f'<li>{n}</li>'

    intraday_section = ""
    if intraday and rankings:
        up_rows = ""
        for i, item in enumerate(rankings.get('up', [])[:10], 1):
            up_rows += f'<tr><td>{i}</td><td>{item["name"]}</td><td>{item["change"]}</td></tr>'
        down_rows = ""
        for i, item in enumerate(rankings.get('down', [])[:10], 1):
            down_rows += f'<tr><td>{i}</td><td>{item["name"]}</td><td>{item["change"]}</td></tr>'
        intraday_section = f'''
        <div class="card">
          <h2>📊 当日の市場状況</h2>
          <table class="kv">
            <tr><td>日経平均</td><td>{intraday['nikkei']}</td></tr>
            <tr><td>TOPIX</td><td>{intraday['topix']}</td></tr>
            <tr><td>マザーズ</td><td>{intraday['mothers']}</td></tr>
            <tr><td>ドル円</td><td>{intraday['usdjpy']}</td></tr>
          </table>
        </div>
        <div class="card">
          <h2>🔼 当日値上がり率TOP10</h2>
          <table class="rank-table">{up_rows}</table>
        </div>
        <div class="card">
          <h2>🔽 当日値下がり率TOP10</h2>
          <table class="rank-table">{down_rows}</table>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<title>株式情報ダッシュボード</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif;
    background: #f0f2f5; color: #1a1a2e; padding: 12px;
    max-width: 720px; margin: 0 auto; line-height: 1.6; }}
  header {{ background: linear-gradient(135deg, #1F3864, #2E75B6);
    color: white; padding: 20px; border-radius: 12px; margin-bottom: 16px; }}
  header h1 {{ font-size: 20px; margin-bottom: 6px; }}
  header .updated {{ font-size: 13px; opacity: 0.9; }}
  .card {{ background: white; border-radius: 12px; padding: 16px;
    margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .card.gc {{ border-left: 4px solid #E8A317; }}
  .card h2 {{ font-size: 17px; color: #1F3864; margin-bottom: 12px;
    padding-bottom: 8px; border-bottom: 2px solid #e0e6ed; }}
  .rank-item, .gc-item {{ padding: 10px; border-bottom: 1px solid #eee;
    display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }}
  .rank-num {{ background: #1F3864; color: white; border-radius: 6px;
    padding: 2px 10px; font-weight: bold; font-size: 14px; }}
  .rank-name, .gc-name {{ font-weight: bold; font-size: 15px; }}
  .rank-score {{ color: #C00000; font-size: 13px; margin-left: auto; }}
  .gc-price {{ font-size: 14px; color: #333; }}
  .gc-src {{ font-size: 11px; color: #fff; background: #E8A317;
    border-radius: 4px; padding: 1px 6px; margin-left: auto; }}
  .rank-reason {{ width: 100%; font-size: 13px; color: #666; margin-top: 4px; }}
  .gc-subtitle {{ font-size: 14px; font-weight: bold; color: #E8A317;
    margin: 10px 0 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  table.kv td {{ padding: 6px 8px; border-bottom: 1px solid #f0f0f0; }}
  table.kv td:first-child {{ color: #666; width: 40%; }}
  table.kv td:last-child {{ font-weight: bold; text-align: right; }}
  table.rank-table td {{ padding: 6px 8px; border-bottom: 1px solid #f0f0f0; }}
  table.rank-table td:first-child {{ width: 32px; color: #999; }}
  table.rank-table td:last-child {{ text-align: right; font-weight: bold; }}
  ul {{ list-style: none; }}
  ul li {{ padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
  ul li:before {{ content: "🔸 "; }}
  .premium li:before {{ content: "🏆 "; }}
  .empty {{ color: #aaa; font-style: italic; }}
  .disclaimer {{ background: #FFF4CE; border: 1px solid #e0d090;
    border-radius: 8px; padding: 10px; font-size: 12px;
    color: #806600; margin-bottom: 14px; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  @media (max-width: 600px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
  footer {{ text-align: center; font-size: 12px; color: #999; padding: 16px; }}
</style>
</head>
<body>
  <header>
    <h1>📈 株式情報ダッシュボード</h1>
    <div class="updated">{mode_label} ／ 最終更新: {date_str}</div>
  </header>

  <div class="disclaimer">
    ※「注目銘柄TOP5」「ゴールデンクロス銘柄」は複数指標を機械的にスコア化・抽出した結果で、買い推奨ではありません。テクニカル指標は将来を保証しません。投資判断はご自身の責任でお願いします。
  </div>

  <div class="card">
    <h2>📈 本日の注目銘柄TOP5</h2>
    {top5_html}
  </div>

  <div class="card gc">
    <h2>⚡ ゴールデンクロス銘柄</h2>
    <div class="gc-subtitle">【5日 × 25日 GC】</div>
    {gc_short_html}
    <div class="gc-subtitle">【25日 × 75日 GC（中期）】</div>
    {gc_mid_html}
  </div>

  <div class="card">
    <h2>🏆 超絶決算情報</h2>
    <ul class="premium">{earnings_html}</ul>
  </div>

  {intraday_section}

  <div class="card">
    <h2>🌅 寄り付き予想</h2>
    <table class="kv">
      <tr><td>日経225先物(CME)</td><td>{market['nikkei_fut']}</td></tr>
      <tr><td>ドル円</td><td>{market['usdjpy']}</td></tr>
      <tr><td>WTI原油</td><td>{market['wti']}</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>🇺🇸 米国市場（前夜）</h2>
    <table class="kv">
      <tr><td>NYダウ</td><td>{market['dow']}</td></tr>
      <tr><td>ナスダック</td><td>{market['nasdaq']}</td></tr>
      <tr><td>SOX指数</td><td>{market['sox']}</td></tr>
      <tr><td>VIX</td><td>{market['vix']}</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>🌏 ADR日本株</h2>
    <table class="kv">{adr_html}</table>
  </div>

  <div class="grid2">
    <div class="card">
      <h2>🔼 PTS夜間 上昇</h2>
      <table class="rank-table">{pts_up_html}</table>
    </div>
    <div class="card">
      <h2>🔽 PTS夜間 下落</h2>
      <table class="rank-table">{pts_down_html}</table>
    </div>
  </div>

  <div class="card">
    <h2>📰 注目ニュース</h2>
    <ul>{news_html}</ul>
  </div>

  <footer>
    自動更新：平日 朝6:30 ／ 引け前14:45<br>
    Powered by GitHub Actions + GitHub Pages
  </footer>
</body>
</html>'''


if __name__ == "__main__":
    main()
