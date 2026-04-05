from bot.exchange import get_price, get_ohlcv
from bot.signals import get_signal

print("🔄 Test du bot...")

# Test prix
price = get_price("BTC/USDT")
print(f"💰 Prix BTC/USDT : {price}")

# Test signal
signal = get_signal("BTC/USDT")
print(f"📡 Signal : {signal}")

print("✅ Test terminé !")
