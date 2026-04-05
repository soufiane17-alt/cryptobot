from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import load_portfolio, execute_paper_trade
import time

app = FastAPI(title="CryptoBot Prototype Simulator")

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
  <title>CryptoBot — Trading Simulator (Prototype)</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root { --bg: #0d0d0d; --card: #141414; --border: rgba(255,255,255,0.1); --green: #22c55e; --red: #ef4444; --text: #f0f0f0; }
    body { background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; margin:0; padding:0; }
    .header { background: #111; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
    .logo { font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 20px 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 14px 10px; text-align: left; border-bottom: 1px solid var(--border); }
    .buy { color: var(--green); font-weight: 600; }
    .sell { color: var(--red); font-weight: 600; }
    button { background: #22c55e; color: black; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }
    button:hover { background: #16a34a; }
  </style>
</head>
<body>
<div class="header">
  <div class="logo">CryptoBot Simulator</div>
  <div>Portefeuille : <strong id="balance">10 000</strong> USDT</div>
</div>

<div style="max-width:1200px; margin: 0 auto; padding: 20px;">
  <div class="card">
    <h2>Prix en temps réel</h2>
    <div id="prices" style="font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem;"></div>
  </div>

  <div class="card">
    <h2>Derniers signaux</h2>
    <table>
      <thead>
        <tr><th>Heure</th><th>Paire</th><th>Signal</th><th>RSI</th><th>Score</th><th>Raison</th><th>Action</th></tr>
      </thead>
      <tbody id="signals"></tbody>
    </table>
  </div>

  <div class="card">
    <h2>Historique des trades simulés</h2>
    <table>
      <thead>
        <tr><th>Date</th><th>Action</th><th>Paire</th><th>Prix</th><th>Montant</th></tr>
      </thead>
      <tbody id="history"></tbody>
    </table>
  </div>
</div>

<script>
  async function update() {
    const res = await fetch('/api/status');
    const data = await res.json();

    // Prix
    document.getElementById('prices').innerHTML = `
      BTC/USDT : $${Number(data.btc_price).toLocaleString('fr-FR')}<br>
      ETH/USDT : $${Number(data.eth_price).toLocaleString('fr-FR')}<br>
      SOL/USDT : $${Number(data.sol_price).toLocaleString('fr-FR')}
    `;

    // Solde
    document.getElementById('balance').textContent = Number(data.portfolio.usdt).toLocaleString('fr-FR');

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
        <td><button onclick="trade('${s.symbol}', '${s.signal}', 150)">Trader 150$</button></td>
      </tr>`;
    });
    document.getElementById('signals').innerHTML = html || '<tr><td colspan="7" style="text-align:center; color:#666;">Aucun signal pour le moment</td></tr>';

    // Historique
    let hist = '';
    data.portfolio.history.slice(-8).reverse().forEach(t => {
      hist += `<tr>
        <td>${t.timestamp.slice(11,19)}</td>
        <td class="${t.side.toLowerCase()}">${t.side}</td>
        <td>${t.symbol}</td>
        <td>$${Number(t.price).toLocaleString('fr-FR')}</td>
        <td>$${Number(t.amount_usdt).toLocaleString('fr-FR')}</td>
      </tr>`;
    });
    document.getElementById('history').innerHTML = hist;
  }

  async function trade(symbol, side, amount) {
    await fetch('/api/trade', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({symbol, side, amount})
    });
    update();
  }

  setInterval(update, 4000);
  update();
</script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML_DASHBOARD)

@app.get("/api/status")
async def status():
    portfolio = load_portfolio()
    return {
        "btc_price": get_price("BTC/USDT"),
        "eth_price": get_price("ETH/USDT"),
        "sol_price": get_price("SOL/USDT"),
        "recent_signals": [{**get_signal(sym), "symbol": sym} for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]],
        "portfolio": portfolio
    }

@app.post("/api/trade")
async def api_trade(data: dict):
    result = execute_paper_trade(data["symbol"], data["side"], data["amount"])
    return result
