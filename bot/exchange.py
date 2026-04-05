import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

# Mode public (lecture seule, sans clé API pour le moment)
exchange = ccxt.binance({
    "enableRateLimit": True,   # évite de se faire bloquer par Binance
    # On laisse les clés vides pour l'instant (on les mettra plus tard)
})

def get_price(symbol="BTC/USDT"):
    """Récupère le prix actuel"""
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]

def get_ohlcv(symbol="BTC/USDT", timeframe="1h", limit=200):
    """Récupère les données historiques"""
    data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return data

print("✅ Connexion Binance en mode public prête")
