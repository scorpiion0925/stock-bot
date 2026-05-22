"""
注目銘柄TOP5を複数指標から算出（テクニカル対応版）
PTS需給 × 決算ファンダ × テクニカル の3点でスコアリング。
"""
from technical import analyze_ticker, tech_score


def get_top5_attention(pts_data, earnings_data):
    scores = {}

    for item in pts_data.get('up', [])[:15]:
        name = item['name']
        code = item.get('code', '')
        if name not in scores:
            scores[name] = {"code": code, "score": 0, "reasons": []}
        pts_score = min(item.get('change_pct', 0) * 3, 30)
        scores[name]['score'] += pts_score
        scores[name]['reasons'].append(f"PTS{item['change']}")

    for e in earnings_data.get('top', []):
        code = e.get('code', '')
        if not code:
            continue
        matched_name = None
        for name, data in scores.items():
            if data.get('code') == code:
                matched_name = name
                break
        if matched_name:
            scores[matched_name]['score'] += min(e['score'], 40)
            short = e['headline'][:30] + ("..." if len(e['headline']) > 30 else "")
            scores[matched_name]['reasons'].append(short)
        else:
            short = e['headline'][:40] + ("..." if len(e['headline']) > 40 else "")
            display_name = f"({code}) " + (short.split()[0] if short else "")
            scores[display_name] = {"code": code, "score": min(e['score'], 40),
                                    "reasons": [short]}

    # テクニカルスコアを加算
    for name, data in scores.items():
        code = data.get('code', '')
        if not code:
            continue
        try:
            analysis = analyze_ticker(f"{code}.T")
            ts, treasons = tech_score(analysis)
            if ts > 0:
                data['score'] += ts
                data['reasons'].extend(treasons)
        except Exception as ex:
            print(f"テクニカル計算スキップ {code}: {ex}")

    ranked = sorted(scores.items(), key=lambda x: -x[1]['score'])
    top5 = []
    for name, data in ranked[:5]:
        if data['score'] < 10:
            continue
        reason_str = " / ".join(data['reasons'][:4])
        top5.append({"name": name, "code": data['code'],
                    "score": data['score'],
                    "reason": reason_str if reason_str else "市場の話題銘柄"})
    return top5
