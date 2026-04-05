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
    # Portefeuille initial
    return {
        "usdt": 10000.0,          # 10 000$ virtuels
        "positions": {},          # ex: {"BTC/USDT": {"amount": 0.15, "entry_price": 65000}}
        "history": []             # liste des trades
    }

def save_portfolio(portfolio):
    os.makedirs("db", exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)

def execute_paper_trade(symbol, side, amount_usdt):
    """Exécute un trade simulé avec l'argent virtuel"""
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
        portfolio["positions"][symbol]["entry_price"] = price  # moyenne simple

    elif side == "SELL":
        if symbol not in portfolio["positions"] or portfolio["positions"][symbol]["amount"] <= 0:
            return {"status": "error", "message": "Pas de position à vendre"}
        amount_crypto = portfolio["positions"][symbol]["amount"]
        portfolio["usdt"] += amount_crypto * price
        portfolio["positions"][symbol]["amount"] = 0

    # Enregistre l'historique
    trade = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "side": side,
        "price": price,
        "amount_usdt": amount_usdt if side == "BUY" else amount_crypto * price
    }
    portfolio["history"].append(trade)

    save_portfolio(portfolio)
    return {"status": "success", "trade": trade, "portfolio": portfolio}
