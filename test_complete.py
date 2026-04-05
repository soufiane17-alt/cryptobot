from bot.exchange import get_price, get_ohlcv
from bot.signals import get_signal
from bot.telegram import send_alert, format_signal

print("🚀 Test complet du CryptoBot...")

# 1. Prix actuel
price = get_price("BTC/USDT")
print(f"💰 Prix BTC/USDT : {price}")

# 2. Signal
signal = get_signal("BTC/USDT")
print(f"📡 Signal généré : {signal['signal']} - RSI {signal['rsi']}")

# 3. Formatage + alerte (même si Telegram n'est pas configuré)
message = format_signal(signal, "BTC/USDT")
print(f"\n📨 Message qui serait envoyé :\n{message}")

print("\n✅ Test complet terminé !")
