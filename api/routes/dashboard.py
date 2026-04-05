from fastapi import APIRouter
from bot.exchange import get_price
from bot.signals import get_signal
import time

router = APIRouter(prefix="/api", tags=["dashboard"])

@router.get("/status")
async def get_status():
    try:
        btc_price = get_price("BTC/USDT")
        eth_price = get_price("ETH/USDT")
        sol_price = get_price("SOL/USDT")

        # Derniers signaux
        signals = []
        for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
            signal = get_signal(symbol)
            signals.append({
                "symbol": symbol,
                "signal": signal["signal"],
                "rsi": float(signal["rsi"]),
                "reason": signal["reason"],
                "timestamp": time.time()
            })

        return {
            "status": "online",
            "btc_price": round(btc_price, 2),
            "eth_price": round(eth_price, 2),
            "sol_price": round(sol_price, 2),
            "recent_signals": signals,
            "last_update": time.time()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
