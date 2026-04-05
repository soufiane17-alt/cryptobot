import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

# Bybit est beaucoup plus fiable depuis Railway
exchange = ccxt.bybit({
    'enableRateLimit': True,
})

def get_price(symbol="BTC/USDT"):
    """Récupère le prix actuel"""
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]

def get_ohlcv(symbol="BTC/USDT", timeframe="15m", limit=200):
    """Récupère les bougies OHLCV"""
    data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return data
