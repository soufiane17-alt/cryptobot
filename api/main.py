import asyncio, time, json, os
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
import ccxt.async_support as ccxt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

EXCHANGE_ID  = os.getenv("EXCHANGE_ID", "binance")
SYMBOLS      = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
REFRESH_SEC  = int(os.getenv("PRICE_REFRESH_SEC", "15"))
SIGNALS_FILE = Path(os.getenv("SIGNALS_FILE", "db/signals.json"))
STATS_FILE   = Path(os.getenv("STATS_FILE",   "db/stats.json"))

cache: dict = {"prices": {}, "signals": [], "stats": {}, "updated_at": 0}
exchange: Optional[ccxt.Exchange] = None

async def get_exchange():
    global exchange
    if exchange is None:
        cls = getattr(ccxt, EXCHANGE_ID)
        exchange = cls({"enableRateLimit": True})
    return exchange

async def fetch_prices():
    ex = await get_exchange()
    tasks = [ex.fetch_ticker(sym) for sym in SYMBOLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    prices = {}
    for sym, result in zip(SYMBOLS, results):
        if isinstance(result, Exception):
            continue
        base = sym.split("/")[0]
        prev = result.get("open") or result["last"]
        last = result["last"]
        change_pct = ((last - prev) / prev * 100) if prev else 0
        prices[base] = {
            "symbol": sym,
            "price":  round(last, 6),
            "change": round(change_pct, 2),
            "volume": round((result.get("quoteVolume") or 0) / 1e9, 2),
            "high":   round(result.get("high") or last, 2),
            "low":    round(result.get("low") or last, 2),
        }
    return prices

def load_signals():
    if SIGNALS_FILE.exists():
        try:
            return json.loads(SIGNALS_FILE.read_text())
        except Exception:
            pass
    return [
        {"time":"03:41","pair":"BTC/USDT","signal":"BUY", "price":83250, "tp":85000,"sl":82000,"tf":"1H", "conf":91,"ts":time.time()-180},
        {"time":"03:33","pair":"SOL/USDT","signal":"SELL","price":119.80,"tp":116.0,"sl":121.5,"tf":"15M","conf":78,"ts":time.time()-660},
        {"time":"03:20","pair":"ETH/USDT","signal":"BUY", "price":1874,  "tp":1950, "sl":1840, "tf":"4H", "conf":85,"ts":time.time()-1440},
        {"time":"03:06","pair":"BNB/USDT","signal":"BUY", "price":590.50,"tp":610,  "sl":582,  "tf":"1H", "conf":66,"ts":time.time()-2280},
        {"time":"02:52","pair":"BTC/USDT","signal":"SELL","price":82100, "tp":80500,"sl":83200,"tf":"4H", "conf":73,"ts":time.time()-3120},
        {"time":"02:40","pair":"SOL/USDT","signal":"WATCH","price":120.10,"tp":None,"sl":None, "tf":"1D", "conf":54,"ts":time.time()-3960},
    ]

def load_stats():
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text())
        except Exception:
            pass
    return {"win_rate":68.4,"total_trades":247,"pnl_usd":4218,"open_trades":3,"period_days":30}

async def price_refresh_loop():
    while True:
        try:
            cache["prices"] = await fetch_prices()
            cache["updated_at"] = time.time()
        except Exception as e:
            print(f"[PriceFetch] Erreur: {e}")
        await asyncio.sleep(REFRESH_SEC)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        cache["prices"] = await fetch_prices()
        cache["updated_at"] = time.time()
    except Exception as e:
        print(f"[Startup] {e}")
    asyncio.create_task(price_refresh_loop())
    yield
    if exchange:
        await exchange.close()

app = FastAPI(title="CryptoBot API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

static_dir = Path("frontend/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", include_in_schema=False)
async def root():
    html = static_dir / "index.html"
    if html.exists():
        return FileResponse(str(html))
    return JSONResponse({"status": "CryptoBot API running"})

@app.get("/api/prices")
async def api_prices():
    if not cache["prices"]:
        raise HTTPException(503, "Prix non disponibles")
    return {"data": cache["prices"], "updated_at": cache["updated_at"], "exchange": EXCHANGE_ID}

@app.get("/api/signals")
async def api_signals():
    signals = load_signals()
    return {"data": signals[:20], "count": len(signals)}

@app.get("/api/stats")
async def api_stats():
    return load_stats()

@app.get("/api/status")
async def api_status():
    return {"status":"online","exchange":EXCHANGE_ID,"symbols":SYMBOLS,
            "last_price_fetch": datetime.fromtimestamp(cache["updated_at"],tz=timezone.utc).isoformat() if cache["updated_at"] else None}
