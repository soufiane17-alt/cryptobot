import time
from datetime import datetime
from bot.exchange import get_price
from bot.signals import get_signal
from bot.telegram import send_alert, format_signal

print("🚀 CryptoBot IA démarré - Mode boucle 30 secondes")
print("=" * 70)

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

while True:
    try:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] 🔄 Analyse en cours...")

        for symbol in SYMBOLS:
            signal = get_signal(symbol)
            price = get_price(symbol)
            
            print(f"   {symbol:10} | Prix: {price:,.0f} | Signal: {signal['signal']:4} (RSI {signal['rsi']:5.1f})")

            if signal["signal"] in ["BUY", "SELL"]:
                message = format_signal(signal, symbol)
                send_alert(f"🕒 {now}\n{message}")
                print(f"   ✅ Alerte envoyée sur Telegram pour {symbol}")

        print("-" * 70)
        print("⏳ Prochaine analyse dans 30 secondes...\n")
        
        time.sleep(30)   # 30 secondes

    except Exception as e:
        print(f"❌ Erreur : {e}")
        time.sleep(10)
