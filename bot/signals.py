import pandas as pd
import numpy as np
from bot.exchange import get_ohlcv
import time

def calculate_rsi(closes, period=14):
    delta = pd.Series(closes).diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(closes):
    series = pd.Series(closes)
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    histogram = macd - signal
    return macd, signal, histogram

def calculate_bollinger(closes, period=20, std=2):
    series = pd.Series(closes)
    sma = series.rolling(period).mean()
    std_dev = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, lower, sma

def calculate_ema(closes, period=50):
    return pd.Series(closes).ewm(span=period).mean()

def analyze_timeframe(closes):
    rsi = calculate_rsi(closes)
    macd, macd_signal, histogram = calculate_macd(closes)
    upper_bb, lower_bb, sma_bb = calculate_bollinger(closes)
    ema50 = calculate_ema(closes)

    last_rsi = rsi.iloc[-1]
    last_macd = macd.iloc[-1]
    last_macd_signal = macd_signal.iloc[-1]
    last_histogram = histogram.iloc[-1]
    last_price = closes[-1]
    last_upper_bb = upper_bb.iloc[-1]
    last_lower_bb = lower_bb.iloc[-1]
    last_ema50 = ema50.iloc[-1]

    score = 50
    if last_rsi < 22: score += 32
    elif last_rsi < 30: score += 24
    elif last_rsi > 78: score -= 32
    elif last_rsi > 70: score -= 24

    if last_macd > last_macd_signal and macd.iloc[-2] <= macd_signal.iloc[-2]:
        score += 28
    if last_histogram > 0 and histogram.iloc[-2] <= 0:
        score += 15

    if last_price < last_lower_bb: score += 24
    elif last_price > last_upper_bb: score -= 22

    if last_price > last_ema50: score += 16
    else: score -= 10

    if last_rsi < 28 and last_price < last_lower_bb and last_macd > last_macd_signal:
        score += 18

    score = min(100, max(0, int(score)))

    if score >= 85 and last_rsi < 33:
        signal = "BUY"
    elif score >= 82 and last_rsi > 72:
        signal = "SELL"
    elif score >= 72:
        signal = "BUY" if last_price > last_ema50 else "SELL"
    else:
        signal = "HOLD"

    return {"signal": signal, "score": score, "rsi": round(last_rsi, 1)}

def get_signal(symbol="BTC/USDT"):
    try:
        # Multi-timeframe local
        tf5m  = [c[4] for c in get_ohlcv(symbol, timeframe='5m', limit=80)]
        tf15m = [c[4] for c in get_ohlcv(symbol, timeframe='15m', limit=80)]
        tf1h  = [c[4] for c in get_ohlcv(symbol, timeframe='1h', limit=80)]

        a5m  = analyze_timeframe(tf5m)
        a15m = analyze_timeframe(tf15m)
        a1h  = analyze_timeframe(tf1h)

        votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        votes[a5m["signal"]] += 1
        votes[a15m["signal"]] += 1
        votes[a1h["signal"]] += 2

        final_signal = max(votes, key=votes.get)
        avg_score = int((a5m["score"] + a15m["score"] + a1h["score"] * 1.5) / 3.5)

        # === OPTION 3 : Filtre de tendance globale sur BTC ===
        btc_4h = [c[4] for c in get_ohlcv("BTC/USDT", timeframe='4h', limit=60)]
        btc_1d = [c[4] for c in get_ohlcv("BTC/USDT", timeframe='1d', limit=30)]
        ema50_4h = calculate_ema(btc_4h).iloc[-1]
        ema50_1d = calculate_ema(btc_1d).iloc[-1]
        btc_trend = "BULL" if btc_4h[-1] > ema50_4h and btc_1d[-1] > ema50_1d else "BEAR" if btc_4h[-1] < ema50_4h and btc_1d[-1] < ema50_1d else "NEUTRAL"

        # On filtre les signaux contraires à la tendance globale
        if btc_trend == "BEAR" and final_signal == "BUY":
            final_signal = "HOLD"
            reason = f"Tendance BTC baissière - signal bloqué ({avg_score}/100)"
        elif btc_trend == "BULL" and final_signal == "SELL":
            final_signal = "HOLD"
            reason = f"Tendance BTC haussière - signal bloqué ({avg_score}/100)"
        else:
            reason = f"Signal FORT multi-TF + tendance BTC ({avg_score}/100)"

        return {
            "signal": final_signal,
            "rsi": round(a5m["rsi"], 1),
            "score": avg_score,
            "reason": reason,
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {"signal": "HOLD", "rsi": 50.0, "score": 0, "reason": "Erreur multi-TF", "timestamp": int(time.time())}
