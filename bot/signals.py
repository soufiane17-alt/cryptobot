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

def get_signal(symbol="BTC/USDT"):
    try:
        ohlcv = get_ohlcv(symbol, limit=100)
        closes = [c[4] for c in ohlcv]
        
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

        # === SCORING V5 - ÉQUILIBRÉ ET COHÉRENT ===
        score = 48

        # RSI (priorité forte mais pas extrême)
        if last_rsi < 25: score += 35
        elif last_rsi < 32: score += 25
        elif last_rsi > 78: score -= 35
        elif last_rsi > 70: score -= 25

        # MACD (confirmation très importante)
        if last_macd > last_macd_signal and macd.iloc[-2] <= macd_signal.iloc[-2]:
            score += 30
        if last_histogram > 0 and histogram.iloc[-2] <= 0:
            score += 18

        # Bollinger
        if last_price < last_lower_bb: score += 28
        elif last_price > last_upper_bb: score -= 25

        # EMA50 (tendance générale)
        if last_price > last_ema50: score += 16
        else: score -= 10

        # Bonus convergence forte (seulement si plusieurs signaux alignés)
        if last_rsi < 30 and last_price < last_lower_bb and last_macd > last_macd_signal:
            score += 20

        score = min(100, max(0, int(score)))

        # === DÉCISION FINALE ===
        if score >= 85:
            signal = "BUY" if last_price < last_ema50 * 1.015 else "SELL"
            reason = f"Signal TRÈS FORT {score}/100"
        elif score >= 73:
            signal = "BUY" if last_price > last_ema50 else "SELL"
            reason = f"Signal moyen {score}/100"
        else:
            signal = "HOLD"
            reason = f"Conditions insuffisantes ({score}/100)"

        return {
            "signal": signal,
            "rsi": round(last_rsi, 1),
            "score": score,
            "reason": reason,
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {"signal": "HOLD", "rsi": 50.0, "score": 0, "reason": "Erreur calcul", "timestamp": int(time.time())}
