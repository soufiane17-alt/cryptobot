from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import load_portfolio, execute_paper_trade
import time

app = FastAPI(title="CryptoBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CryptoBot — Prototype Trading Simulator</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root { --bg: #0d0d0d; --card: #141414; --border: rgba(255,255,255,0.1); --green: #22c55e; --red: #ef4444; }
    body { background: var(--bg); color: #f0f0f0; font-family: 'IBM Plex Sans', sans-serif; margin:0; padding:0; }
    .header { background: #111; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 15px 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); }
    .buy { color: var(--green); }
    .sell { color: var(--red); }
  </style>
</head>
<body>
<div class="header">
  <h1>CryptoBot — Trading Simulator (Prototype)</h1>
  <div id="portfolio">Portefeuille : <span id="balance">0</span> USDT</div>
</div>

<div style="padding:20px; max-width:1200px; margin:auto;">
  <div class="card">
    <h2>Prix en temps réel</h2>
    <div id="prices"></div>
  </div>

  <div class="card">
    <h2>Derniers signaux</h2>
    <table><thead><tr><th>Heure</th><th>Paire</th><th>Signal</th><th>RSI</th><th>Score</th><th>Raison</th><th>Action</th></tr></thead><tbody id="signals"></tbody></table>
  </div>

  <div class="card">
    <h2>Historique des trades simulés</h2>
    <table><thead><tr><th>Date</th><th>Action</th><th>Paire</th><th>Prix</th><th>Montant</th></tr></thead><tbody id="history"></tbody></table>
  </div>
</div>

<script>
  async function updateAll() {
    const res = await fetch('/api/status');
    const data = await res.json();

    // Prix
    document.getElementById('prices').innerHTML = `
      BTC/USDT : $${Number(data.btc_price).toLocaleString('fr-FR')}<br>
      ETH/USDT : $${Number(data.eth_price).toLocaleString('fr-FR')}<br>
      SOL/USDT : $${Number(data.sol_price).toLocaleString('fr-FR')}
    `;

    // Signaux
    let html = '';
    data.recent_signals.forEach(s => {
      html += `<tr>
        <td>${new Date(s.timestamp*1000).toLocaleTimeString('fr-FR')}</td>
        <td>${s.symbol}</td>
        <td class="${s.signal.toLowerCase()}">${s.signal}</td>
        <td>${s.rsi}</td>
        <td>${s.score}/100</td>
        <td>${s.reason}</td>
        <td><button onclick="executeTrade('${s.symbol}', '${s.signal}', 100)">Trader 100$</button></td>
      </tr>`;
    });
    document.getElementById('signals').innerHTML = html;

    // Portfolio
    document.getElementById('balance').textContent = data.portfolio.usdt.toLocaleString('fr-FR');

    // Historique
    let hist = '';
    data.portfolio.history.slice(-10).reverse().forEach(t => {
      hist += `<tr><td>${t.timestamp.slice(11,16)}</td><td>${t.side}</td><td>${t.symbol}</td><td>$${t.price}</td><td>$${t.amount_usdt}</td></tr>`;
    });
    document.getElementById('history').innerHTML = hist;
  }

  async function executeTrade(symbol, side, amount) {
    await fetch('/api/trade', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({symbol, side, amount})
    });
    updateAll();
  }

  setInterval(updateAll, 5000);
  updateAll();
</script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML_DASHBOARD)

@app.get("/api/status")
async def status():
    try:
        portfolio = load_portfolio()
        return {
            "btc_price": get_price("BTC/USDT"),
            "eth_price": get_price("ETH/USDT"),
            "sol_price": get_price("SOL/USDT"),
            "recent_signals": [{**get_signal(sym), "symbol": sym} for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]],
            "portfolio": portfolio
        }
    except:
        return {"btc_price": 0, "eth_price": 0, "sol_price": 0, "recent_signals": [], "portfolio": {"usdt": 10000, "positions": {}, "history": []}}

@app.post("/api/trade")
async def trade(data: dict):
    result = execute_paper_trade(data["symbol"], data["side"], data["amount"])
    return result
