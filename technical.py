"""
テクニカル指標の計算モジュール
yfinanceの株価データから各指標を自前計算する（pandas/numpyのみ）。
"""
import pandas as pd
import numpy as np
import yfinance as yf


def get_price_history(ticker_symbol, period="6mo"):
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period=period)
        if len(hist) < 80:
            return None
        return hist
    except Exception as e:
        print(f"株価取得失敗 {ticker_symbol}: {e}")
        return None


def calc_sma(series, window):
    return series.rolling(window=window).mean()


def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line


def calc_bollinger(series, window=20, num_std=2):
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return sma + (std * num_std), sma, sma - (std * num_std)


def calc_ichimoku(hist):
    high = hist['High']
    low = hist['Low']
    conv = (high.rolling(9).max() + low.rolling(9).min()) / 2
    base = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = (conv + base) / 2
    span_b = (high.rolling(52).max() + low.rolling(52).min()) / 2
    return conv, base, span_a, span_b


def analyze_ticker(ticker_symbol):
    hist = get_price_history(ticker_symbol)
    if hist is None:
        return None
    close = hist['Close']
    volume = hist['Volume']

    sma5 = calc_sma(close, 5)
    sma25 = calc_sma(close, 25)
    sma75 = calc_sma(close, 75)
    rsi = calc_rsi(close, 14)
    macd_line, signal_line, _ = calc_macd(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger(close)
    conv, base, span_a, span_b = calc_ichimoku(hist)

    price = close.iloc[-1]
    gc_5_25 = (sma5.iloc[-2] <= sma25.iloc[-2]) and (sma5.iloc[-1] > sma25.iloc[-1])
    gc_25_75 = (sma25.iloc[-2] <= sma75.iloc[-2]) and (sma25.iloc[-1] > sma75.iloc[-1])
    macd_buy = (macd_line.iloc[-2] <= signal_line.iloc[-2]) and \
               (macd_line.iloc[-1] > signal_line.iloc[-1])
    cloud_top = max(span_a.iloc[-1], span_b.iloc[-1])
    above_cloud = price > cloud_top if not pd.isna(cloud_top) else False
    vol5 = volume.rolling(5).mean().iloc[-1]
    vol25 = volume.rolling(25).mean().iloc[-1]
    vol_surge = (vol5 / vol25) if vol25 > 0 else 1.0

    return {
        "latest": {"price": price, "rsi": rsi.iloc[-1]},
        "gc_5_25": gc_5_25, "gc_25_75": gc_25_75,
        "macd_buy": macd_buy, "above_cloud": above_cloud,
        "vol_surge": vol_surge, "rsi_val": rsi.iloc[-1],
    }


def tech_score(analysis):
    if analysis is None:
        return 0, []
    score = 0
    reasons = []
    if analysis["gc_5_25"]:
        score += 12
        reasons.append("GC(5×25)")
    if analysis["macd_buy"]:
        score += 8
        reasons.append("MACD買い")
    rsi = analysis["rsi_val"]
    if not pd.isna(rsi) and 30 <= rsi <= 50:
        score += 5
        reasons.append(f"RSI{rsi:.0f}回復圏")
    if analysis["above_cloud"]:
        score += 5
        reasons.append("雲の上")
    return min(score, 30), reasons


def format_tech_summary(analysis):
    if analysis is None:
        return "データ不足"
    parts = []
    rsi = analysis["rsi_val"]
    if not pd.isna(rsi):
        parts.append(f"RSI:{rsi:.0f}")
    parts.append("MACD:" + ("買い" if analysis["macd_buy"] else "中立"))
    parts.append("雲:" + ("上" if analysis["above_cloud"] else "下/中"))
    return " ".join(parts)
