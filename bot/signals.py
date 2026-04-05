import pandas as pd
import numpy as np
from bot.exchange import get_ohlcv

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
    upper = sma + std * std_dev
    lower = sma - std * std_dev
    return upper, sma, lower

def calculate_ema(closes, period=50):
    return pd.Series(closes).ewm(span=period).mean()

def get_signal(symbol="BTC/USDT"):
    ohlcv = get_ohlcv(symbol, timeframe="15m", limit=200)
    closes = [c[4] for c in ohlcv]
    
    rsi = calculate_rsi(closes)
    macd, macd_signal = calculate_macd(closes)
    upper, middle, lower = calculate_bollinger(closes)
    ema50 = calculate_ema(closes)
    
    last_rsi = rsi.iloc[-1]
    last_price = closes[-1]
    last_upper = upper.iloc[-1]
    last_lower = lower.iloc[-1]
    last_ema50 = ema50.iloc[-1]
    
    macd_cross = macd.iloc[-1] > macd_signal.iloc[-1]
    prev_cross = macd.iloc[-2] <= macd_signal.iloc[-2]
    bullish_cross = macd_cross and not prev_cross
    
    score = 0
    reasons = []
    
    # RSI
    if last_rsi < 30:
        score += 40
        reasons.append("RSI oversold")
    elif last_rsi > 70:
        score -= 40
        reasons.append("RSI overbought")
    
    # MACD
    if bullish_cross:
        score += 30
        reasons.append("MACD bullish cross")
    
    # Bollinger Bands
    if last_price < last_lower:
        score += 25
        reasons.append("Price below lower Bollinger")
    elif last_price > last_upper:
        score -= 25
        reasons.append("Price above upper Bollinger")
    
    # EMA50 trend
    if last_price > last_ema50:
        score += 15
        reasons.append("Above EMA50")
    else:
        score -= 15
        reasons.append("Below EMA50")
    
    # Décision finale
    if score >= 60:
        signal = "BUY"
    elif score <= -50:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    return {
        "signal": signal,
        "rsi": round(last_rsi, 1),
        "score": score,
        "reason": " | ".join(reasons) if reasons else "Aucune condition forte"
    }
