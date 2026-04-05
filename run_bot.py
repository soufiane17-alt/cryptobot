from bot.exchange import get_price
from bot.signals import get_signal
from bot.telegram import send_alert, format_signal
from bot.risk import log_trade, calculate_position_size
import time

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
ACCOUNT_BALANCE = 1000  # Solde simulé

print("🚀 CryptoBot IA démarré - Mode multi-timeframe + risque automatique")

while True:
    print(f"\n[{time.strftime('%H:%M:%S')}] 🔄 Vérification des signaux...")
    for symbol in SYMBOLS:
        signal = get_signal(symbol)
        price = get_price(symbol)

        print(f"   {symbol} | Prix: {price:,.0f} | Signal: {signal['signal']} ({signal['score']}/100)")

        if signal["signal"] in ["BUY", "SELL"]:
            trade = log_trade(symbol, signal["signal"], price, signal["score"], signal["reason"])
            send_alert(f"""
🔔 <b>{signal['signal']} — {symbol}</b>
Prix : ${price:,.2f}
Score : {signal['score']}/100
Raison : {signal['reason']}
Position suggérée : ${trade['position_size']}
Stop-loss : ${trade['stop_loss']}
            """.strip())

    print(f"⏳ Prochaine vérification dans 30 secondes...")
    time.sleep(30)
