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
    """Analyse un seul timeframe et retourne un score + signal"""
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
    if last_rsi < 25: score += 32
    elif last_rsi < 32: score += 22
    elif last_rsi > 78: score -= 32
    elif last_rsi > 70: score -= 22

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
        # Analyse sur 3 timeframes
        tf5m  = [c[4] for c in get_ohlcv(symbol, timeframe='5m',  limit=80)]
        tf15m = [c[4] for c in get_ohlcv(symbol, timeframe='15m', limit=80)]
        tf1h  = [c[4] for c in get_ohlcv(symbol, timeframe='1h',  limit=80)]

        analysis_5m  = analyze_timeframe(tf5m)
        analysis_15m = analyze_timeframe(tf15m)
        analysis_1h  = analyze_timeframe(tf1h)

        # Compte les votes
        votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        votes[analysis_5m["signal"]] += 1
        votes[analysis_15m["signal"]] += 1
        votes[analysis_1h["signal"]] += 2   # 1h a plus de poids

        # Signal final
        final_signal = max(votes, key=votes.get)
        avg_score = int((analysis_5m["score"] + analysis_15m["score"] + analysis_1h["score"] * 1.5) / 3.5)

        if final_signal == "HOLD" or avg_score < 70:
            reason = f"Conditions insuffisantes (multi-TF {avg_score}/100)"
        elif final_signal == "BUY":
            reason = f"Signal FORT multi-TF {avg_score}/100"
        else:
            reason = f"Signal FORT multi-TF {avg_score}/100"

        return {
            "signal": final_signal,
            "rsi": round(analysis_5m["rsi"], 1),
            "score": avg_score,
            "reason": reason,
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {"signal": "HOLD", "rsi": 50.0, "score": 0, "reason": "Erreur multi-timeframe", "timestamp": int(time.time())}
