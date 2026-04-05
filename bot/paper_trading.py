import json
import os
from datetime import datetime
from bot.exchange import get_price

PORTFOLIO_FILE = "db/portfolio.json"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "usdt": 10000.0,
        "positions": {},
        "history": []
    }

def save_portfolio(portfolio):
    os.makedirs("db", exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)

def get_current_pnl(portfolio):
    """Calcule le P&L total (réalisé + non réalisé)"""
    total_pnl = 0.0
    positions_value = 0.0

    for symbol, pos in portfolio.get("positions", {}).items():
        if pos.get("amount", 0) > 0:
            current_price = get_price(symbol)
            entry_price = pos.get("entry_price", current_price)
            pnl = (current_price - entry_price) * pos["amount"]
            total_pnl += pnl
            positions_value += current_price * pos["amount"]

    total_balance = portfolio.get("usdt", 0) + positions_value
    return {
        "total_balance": round(total_balance, 2),
        "unrealized_pnl": round(total_pnl, 2),
        "usdt": round(portfolio.get("usdt", 0), 2)
    }

def execute_paper_trade(symbol, side, amount_usdt):
    portfolio = load_portfolio()
    price = get_price(symbol)

    if side == "BUY":
        if portfolio["usdt"] < amount_usdt:
            return {"status": "error", "message": "Pas assez d'USDT"}
        amount_crypto = amount_usdt / price
        portfolio["usdt"] -= amount_usdt
        if symbol not in portfolio["positions"]:
            portfolio["positions"][symbol] = {"amount": 0, "entry_price": price}
        portfolio["positions"][symbol]["amount"] += amount_crypto
        portfolio["positions"][symbol]["entry_price"] = price

    elif side == "SELL":
        if symbol not in portfolio["positions"] or portfolio["positions"][symbol]["amount"] <= 0:
            return {"status": "error", "message": "Pas de position"}
        amount_crypto = portfolio["positions"][symbol]["amount"]
        portfolio["usdt"] += amount_crypto * price
        portfolio["positions"][symbol]["amount"] = 0

    trade = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "side": side,
        "price": price,
        "amount_usdt": amount_usdt if side == "BUY" else amount_crypto * price
    }
    portfolio["history"].append(trade)
    save_portfolio(portfolio)

    return {"status": "success", "trade": trade, "portfolio": portfolio, "pnl": get_current_pnl(portfolio)}
