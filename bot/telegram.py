import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_alert(message: str):
    """Envoie un message sur Telegram"""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️  Clés Telegram non configurées dans .env")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except:
        return False

def format_signal(signal: dict, symbol: str) -> str:
    emoji = "🟢" if signal["signal"] == "BUY" else "🔴" if signal["signal"] == "SELL" else "⚪"
    return f"""{emoji} <b>{signal['signal']} — {symbol}</b>
RSI: {signal['rsi']}
Raison: {signal['reason']}"""
