import json
from datetime import datetime
import os

RISK_FILE = "db/trades.json"

def load_trades():
    if os.path.exists(RISK_FILE):
        try:
            with open(RISK_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_trade(trade):
    trades = load_trades()
    trades.append(trade)
    with open(RISK_FILE, "w") as f:
        json.dump(trades, f, indent=2)

def calculate_position_size(account_balance=1000, risk_percent=1.0, stop_loss_percent=2.0):
    """Calcule la taille de position selon le risque maximal"""
    risk_amount = account_balance * (risk_percent / 100)
    position_size = risk_amount / (stop_loss_percent / 100)
    return round(position_size, 2)

def simulate_stop_loss(entry_price, stop_loss_percent, side="BUY"):
    """Simule le stop-loss"""
    if side == "BUY":
        stop_price = entry_price * (1 - stop_loss_percent / 100)
    else:
        stop_price = entry_price * (1 + stop_loss_percent / 100)
    return round(stop_price, 2)

def log_trade(symbol, side, entry_price, score, reason):
    trade = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "side": side,
        "entry_price": entry_price,
        "score": score,
        "reason": reason,
        "stop_loss": simulate_stop_loss(entry_price, 2.0, side),
        "position_size": calculate_position_size()
    }
    save_trade(trade)
    return trade
