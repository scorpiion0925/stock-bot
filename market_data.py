"""米国市場・為替・先物・ADR情報をyfinanceから取得"""
import yfinance as yf


def fmt(value, suffix=""):
    if value is None:
        return "取得失敗"
    return f"{value:,.2f}{suffix}"


def fmt_change(price, prev_close):
    if price is None or prev_close is None:
        return ""
    change = price - prev_close
    pct = (change / prev_close) * 100
    sign = "+" if change >= 0 else ""
    return f" ({sign}{change:,.2f} / {sign}{pct:.2f}%)"


def get_ticker_summary(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        if len(hist) < 1:
            return None, None
        latest = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) >= 2 else None
        return latest, prev
    except Exception as e:
        print(f"取得失敗 {ticker_symbol}: {e}")
        return None, None


def get_market_summary():
    nikkei_fut, nf_prev = get_ticker_summary("NKD=F")
    usdjpy, _ = get_ticker_summary("JPY=X")
    wti, _ = get_ticker_summary("CL=F")
    dow, dow_prev = get_ticker_summary("^DJI")
    nasdaq, naq_prev = get_ticker_summary("^IXIC")
    sox, sox_prev = get_ticker_summary("^SOX")
    vix, _ = get_ticker_summary("^VIX")

    adr_list = [
        ("トヨタ", "TM"), ("ソニー", "SONY"), ("ホンダ", "HMC"),
        ("三菱UFJ", "MUFG"), ("武田薬品", "TAK"),
    ]
    adrs = []
    for name, sym in adr_list:
        price, prev = get_ticker_summary(sym)
        adrs.append({"name": name, "change": fmt(price) + fmt_change(price, prev)})

    return {
        "nikkei_fut": fmt(nikkei_fut, "円") + fmt_change(nikkei_fut, nf_prev),
        "usdjpy": fmt(usdjpy, "円"),
        "wti": fmt(wti, "ドル"),
        "dow": fmt(dow) + fmt_change(dow, dow_prev),
        "nasdaq": fmt(nasdaq) + fmt_change(nasdaq, naq_prev),
        "sox": fmt(sox) + fmt_change(sox, sox_prev),
        "vix": fmt(vix),
        "adrs": adrs,
    }
