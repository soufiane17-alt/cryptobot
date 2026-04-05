from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import load_portfolio, execute_paper_trade, get_current_pnl
import time

app = FastAPI(title="CryptoBot — Prototype Simulator")

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
    :root { --bg: #0d0d0d; --card: #141414; --border: rgba(255,255,255,0.1); --green: #22c55e; --red: #ef4444; }
    body { background: var(--bg); color: #f0f0f0; font-family: 'IBM Plex Sans', sans-serif; margin:0; padding:0; }
    .header { background: #111; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
    .logo { font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 20px 0; }
    select, button { padding: 8px 12px; background: #222; color: #fff; border: 1px solid var(--border); border-radius: 6px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--border); }
    .buy { color: var(--green); font-weight: 600; }
    .sell { color: var(--red); font-weight: 600; }
    .positive { color: var(--green); }
    .negative { color: var(--red); }
  </style>
</head>
<body>
<div class="header">
  <div class="logo">CryptoBot Simulator (Prototype)</div>
  <div>Solde total : <strong id="total_balance">10 000</strong> USDT <span id="pnl"></span></div>
</div>

<div style="max-width:1350px; margin: 0 auto; padding: 20px;">
  <!-- Sélecteur de graphique -->
  <div class="card">
    <div style="margin-bottom:12px;">
      <strong>Graphique :</strong>
      <button onclick="switchChart('BTC/USDT')" style="margin-right:8px;">BTC</button>
      <button onclick="switchChart('ETH/USDT')" style="margin-right:8px;">ETH</button>
      <button onclick="switchChart('SOL/USDT')">SOL</button>
    </div>
    <canvas id="priceChart" height="160"></canvas>
    <div id="sentiment" style="margin-top:8px; font-size:0.9rem; font-family:monospace;"></div>
  </div>

  <!-- Signaux -->
  <div class="card">
    <h2>Derniers signaux</h2>
    <table>
      <thead><tr><th>Heure</th><th>Paire</th><th>Signal</th><th>RSI</th><th>Score</th><th>Raison</th><th>Action</th></tr></thead>
      <tbody id="signals"></tbody>
    </table>
  </div>

  <!-- Admin / Rapport -->
  <div class="card">
    <h2>📊 Rapport Admin — Évolution du bot en temps réel</h2>
    <div id="admin_report" style="line-height:1.7;"></div>
  </div>

  <!-- Historique -->
  <div class="card">
    <h2>Historique des trades simulés</h2>
    <table>
      <thead><tr><th>Date</th><th>Action</th><th>Paire</th><th>Prix</th><th>Montant</th></tr></thead>
      <tbody id="history"></tbody>
    </table>
  </div>
</div>

<script>
  let currentSymbol = 'BTC/USDT';
  let priceChart;
  let prices = [];
  let timestamps = [];

  async function update() {
    const res = await fetch('/api/status');
    const data = await res.json();

    // Solde + P&L
    document.getElementById('total_balance').textContent = Number(data.portfolio.total_balance).toLocaleString('fr-FR');
    const pnl = data.portfolio.unrealized_pnl;
    document.getElementById('pnl').innerHTML = pnl >= 0 
      ? `<span class="positive">+$${pnl.toLocaleString('fr-FR')}</span>` 
      : `<span class="negative">-$${Math.abs(pnl).toLocaleString('fr-FR')}</span>`;

    // Graphique
    const now = new Date().toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'});
    prices.push(data.btc_price); // on garde BTC comme base, on peut changer plus tard
    timestamps.push(now);
    if (prices.length > 120) { prices.shift(); timestamps.shift(); } // ~2 heures rolling

    if (!priceChart) {
      priceChart = new Chart(document.getElementById('priceChart'), {
        type: 'line',
        data: { labels: timestamps, datasets: [{ label: currentSymbol, data: prices, borderColor: '#22c55e', tension: 0.3, pointRadius: 0 }] },
        options: { scales: { y: { grid: { color: '#222' } }, x: { grid: { color: '#222' } } } }
      });
    } else {
      priceChart.data.labels = timestamps;
      priceChart.data.datasets[0].data = prices;
      priceChart.update('none');
    }

    // Sentiment simple
    document.getElementById('sentiment').innerHTML = `Sentiment actuel ${currentSymbol} : <strong style="color:#eab308">NEUTRAL</strong> (basé sur momentum 1h)`;

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
    document.getElementById('signals').innerHTML = html;

    // Admin report
    document.getElementById('admin_report').innerHTML = `
      <strong>Statistiques du bot en temps réel :</strong><br>
      Total trades : ${data.portfolio.history.length}<br>
      Win rate : -- % (en cours d'apprentissage)<br>
      P&L total : ${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString('fr-FR')}<br>
      Meilleure paire aujourd'hui : SOL<br>
      <small style="color:#666;">Mode prototype - le bot s'entraîne tout seul</small>
    `;

    // Historique
    let hist = '';
    data.portfolio.history.slice(-10).reverse().forEach(t => {
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

  function switchChart(symbol) {
    currentSymbol = symbol;
    update();
  }

  async function trade(symbol, side, amount) {
    await fetch('/api/trade', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({symbol, side, amount}) });
    update();
  }

  setInterval(update, 5000);
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
