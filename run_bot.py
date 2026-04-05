from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import execute_paper_trade, load_portfolio
import time

print("🚀 CryptoBot Simulator - Mode AUTO-ENTRAÎNEMENT activé")
print("Le bot va trader automatiquement avec l'argent virtuel quand le score est assez fort (>= 82)\n")

while True:
    portfolio = load_portfolio()
    print(f"[{time.strftime('%H:%M:%S')}] 💰 Portefeuille : ${portfolio['usdt']:,.2f} USDT")

    for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
        signal = get_signal(symbol)
        price = get_price(symbol)

        print(f"   {symbol} | Prix: ${price:,.2f} | {signal['signal']} ({signal['score']}/100)")

        # Auto-trade si signal assez fort
        if signal["score"] >= 82 and signal["signal"] in ["BUY", "SELL"]:
            amount = 200
            result = execute_paper_trade(symbol, signal["signal"], amount)
            
            if result["status"] == "success":
                print(f"   ✅ AUTO-TRADE : {signal['signal']} {symbol} pour ${amount}")
            else:
                print(f"   ❌ {result.get('message', 'erreur')}")

    print("⏳ Prochaine vérification dans 30 secondes...\n")
    time.sleep(30)
