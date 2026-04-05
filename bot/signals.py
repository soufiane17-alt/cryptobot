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
    return macd, signal

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
        ohlcv = get_ohlcv(symbol)
        closes = [c[4] for c in ohlcv]
        
        rsi = calculate_rsi(closes)
        macd, macd_signal = calculate_macd(closes)
        upper_bb, lower_bb, sma_bb = calculate_bollinger(closes)
        ema50 = calculate_ema(closes)

        last_rsi = rsi.iloc[-1]
        last_macd = macd.iloc[-1]
        last_macd_signal = macd_signal.iloc[-1]
        last_price = closes[-1]
        last_upper_bb = upper_bb.iloc[-1]
        last_lower_bb = lower_bb.iloc[-1]
        last_ema50 = ema50.iloc[-1]

        # Calcul du score de confiance (0-100)
        score = 0

        # RSI
        if last_rsi < 30: score += 35
        elif last_rsi > 70: score += 25
        elif 40 < last_rsi < 60: score += 10

        # MACD crossover
        if last_macd > last_macd_signal and macd.iloc[-2] <= macd_signal.iloc[-2]:
            score += 30
        elif last_macd < last_macd_signal and macd.iloc[-2] >= macd_signal.iloc[-2]:
            score += 20

        # Bollinger Bands
        if last_price < last_lower_bb: score += 20
        elif last_price > last_upper_bb: score += 15

        # EMA50 trend
        if last_price > last_ema50: score += 15
        else: score += 5

        # Score final (max 100)
        score = min(100, max(0, int(score)))

        # Décision finale
        if score >= 75 and last_rsi < 35:
            signal = "BUY"
            reason = f"Score fort {score}/100 - RSI oversold + confirmations"
        elif score >= 75 and last_rsi > 70:
            signal = "SELL"
            reason = f"Score fort {score}/100 - RSI overbought"
        else:
            signal = "HOLD"
            reason = f"Score {score}/100 - Conditions insuffisantes"

        return {
            "signal": signal,
            "rsi": round(last_rsi, 1),
            "score": score,
            "reason": reason,
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {"signal": "HOLD", "rsi": 50, "score": 0, "reason": "Erreur calcul", "timestamp": int(time.time())}
