from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import load_portfolio, execute_paper_trade, get_current_pnl

app = FastAPI(title="CryptoBot Simulator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return HTMLResponse(pathlib.Path("frontend/static/index.html").read_text(encoding="utf-8"))

@app.get("/api/status")
async def status():
    portfolio = load_portfolio()
    pnl = get_current_pnl(portfolio)
    return {
        "btc_price": get_price("BTC/USDT"),
        "eth_price": get_price("ETH/USDT"),
        "sol_price": get_price("SOL/USDT"),
        "recent_signals": [{**get_signal(sym), "symbol": sym} for sym in ["BTC/USDT","ETH/USDT","SOL/USDT"]],
        "portfolio": {**portfolio, **pnl},
    }

@app.post("/api/trade")
async def api_trade(data: dict):
    return execute_paper_trade(data["symbol"], data["side"], data["amount"])
