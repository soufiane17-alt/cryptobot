from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import load_portfolio, execute_paper_trade, get_current_pnl
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
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root { --bg: #0d0d0d; --card: #141414; --border: rgba(255,255,255,0.1); --green: #22c55e; --red: #ef4444; --text: #f0f0f0; }
    body { background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; margin:0; padding:0; }
    .header { background: #111; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
    .logo { font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 20px 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--border); }
    .buy { color: var(--green); }
    .sell { color: var(--red); }
    button { background: #22c55e; color: black; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }
  </style>
</head>
<body>
<div class="header">
  <div class="logo">CryptoBot Simulator</div>
  <div>
    Solde total : <strong id="total_balance">10 000</strong> USDT<br>
    <span id="pnl"></span>
  </div>
</div>

<div style="max-width:1300px; margin: 0 auto; padding: 20px;">
  <!-- Graphique prix en direct -->
  <div class="card">
    <h2>Graphique prix BTC en direct</h2>
    <canvas id="priceChart" height="120"></canvas>
  </div>

  <div class="card">
    <h2>Derniers signaux</h2>
    <table>
      <thead><tr><th>Heure</th><th>Paire</th><th>Signal</th><th>RSI</th><th>Score</th><th>Raison</th><th>Action</th></tr></thead>
      <tbody id="signals"></tbody>
    </table>
  </div>

  <div class="card">
    <h2>Historique des trades + P&L</h2>
    <table>
      <thead><tr><th>Date</th><th>Action</th><th>Paire</th><th>Prix</th><th>Montant</th></tr></thead>
      <tbody id="history"></tbody>
    </table>
  </div>
</div>

<script>
  let priceChart;
  let prices = [];
  let timestamps = [];

  async function update() {
    const res = await fetch('/api/status');
    const data = await res.json();

    // Mise à jour solde + P&L
    document.getElementById('total_balance').textContent = Number(data.portfolio.total_balance).toLocaleString('fr-FR');
    const pnlEl = document.getElementById('pnl');
    const pnl = data.portfolio.unrealized_pnl;
    pnlEl.innerHTML = pnl >= 0 
      ? `<span style="color:#22c55e">+$${pnl.toLocaleString('fr-FR')}</span>` 
      : `<span style="color:#ef4444">-$${Math.abs(pnl).toLocaleString('fr-FR')}</span>`;

    // Graphique prix BTC
    const now = new Date().toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
    prices.push(data.btc_price);
    timestamps.push(now);
    if (prices.length > 60) { prices.shift(); timestamps.shift(); }

    if (!priceChart) {
      const ctx = document.getElementById('priceChart').getContext('2d');
      priceChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: timestamps,
          datasets: [{
            label: 'BTC/USDT',
            data: prices,
            borderColor: '#22c55e',
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 0
          }]
        },
        options: { scales: { y: { grid: { color: '#222' } }, x: { grid: { color: '#222' } } } }
      });
    } else {
      priceChart.data.labels = timestamps;
      priceChart.data.datasets[0].data = prices;
      priceChart.update('none');
    }

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
    document.getElementById('signals').innerHTML = html || '<tr><td colspan="7" style="text-align:center;color:#666;">Aucun signal pour le moment</td></tr>';

    // Historique
    let hist = '';
    data.portfolio.history.slice(-12).reverse().forEach(t => {
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
    await fetch('/api/trade', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({symbol, side, amount}) });
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
    pnl = get_current_pnl(portfolio)
    return {
        "btc_price": get_price("BTC/USDT"),
        "eth_price": get_price("ETH/USDT"),
        "sol_price": get_price("SOL/USDT"),
        "recent_signals": [{**get_signal(sym), "symbol": sym} for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]],
        "portfolio": {**portfolio, **pnl}
    }

@app.post("/api/trade")
async def api_trade(data: dict):
    result = execute_paper_trade(data["symbol"], data["side"], data["amount"])
    return result
