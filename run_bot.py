from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import execute_paper_trade, load_portfolio
import time

print("🚀 CryptoBot Simulator - Mode Auto-Training activé")
print("Le bot va trader automatiquement avec de l'argent virtuel quand le signal est assez fort.")

while True:
    portfolio = load_portfolio()
    print(f"\n[{time.strftime('%H:%M:%S')}] 💰 Portefeuille : ${portfolio['usdt']:,.2f} USDT | Positions : {len(portfolio['positions'])}")

    for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
        signal = get_signal(symbol)
        price = get_price(symbol)

        print(f"   {symbol} | Prix: ${price:,.2f} | {signal['signal']} ({signal['score']}/100) - {signal['reason']}")

        # Trade automatique si signal fort
        if signal["score"] >= 82 and signal["signal"] in ["BUY", "SELL"]:
            amount = 150  # trade de 150$ virtuels par signal fort
            result = execute_paper_trade(symbol, signal["signal"], amount)
            
            if result["status"] == "success":
                print(f"   ✅ TRADE EXÉCUTÉ : {signal['signal']} {symbol} pour ${amount}")
            else:
                print(f"   ❌ Trade impossible : {result['message']}")

    print("⏳ Prochaine vérification dans 30 secondes...")
    time.sleep(30)
