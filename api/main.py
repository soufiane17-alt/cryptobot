from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
from bot.paper_trading import load_portfolio, execute_paper_trade, get_current_pnl
import time

app = FastAPI(title="CryptoBot — Trading Simulator (Prototype)")

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
    :root { --bg: #0d0d0d; --card: #141414; --border: rgba(255,255,255,0.1); --green: #22c55e; --red: #ef4444; }
    body { background: var(--bg); color: #f0f0f0; font-family: 'IBM Plex Sans', sans-serif; margin:0; padding:0; }
    .header { background: #111; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
    .logo { font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 20px 0; }
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
  <div class="logo">CryptoBot Simulator</div>
  <div>Solde total : <strong id="total_balance">10 000</strong> USDT <span id="pnl"></span></div>
</div>

<div style="max-width:1300px; margin:0 auto; padding:20px;">
  <!-- Prix en temps réel -->
  <div class="card">
    <h2>Prix en temps réel</h2>
    <div id="prices" style="font-family:monospace; font-size:1.3rem; line-height:1.8;"></div>
  </div>

  <!-- Positions ouvertes -->
  <div class="card">
    <h2>Positions ouvertes</h2>
    <div id="positions"></div>
  </div>

  <!-- Derniers signaux -->
  <div class="card">
    <h2>Derniers signaux</h2>
    <table>
      <thead><tr><th>Heure</th><th>Paire</th><th>Signal</th><th>RSI</th><th>Score</th><th>Raison</th></tr></thead>
      <tbody id="signals"></tbody>
    </table>
  </div>

  <!-- Historique -->
  <div class="card">
    <h2>Historique des trades</h2>
    <table>
      <thead><tr><th>Date</th><th>Action</th><th>Paire</th><th>Prix</th><th>Montant</th></tr></thead>
      <tbody id="history"></tbody>
    </table>
  </div>
</div>

<script>
  async function update() {
    const res = await fetch('/api/status');
    const data = await res.json();

    // Prix en temps réel
    document.getElementById('prices').innerHTML = `
      BTC/USDT : $${Number(data.btc_price).toLocaleString('fr-FR')}<br>
      ETH/USDT : $${Number(data.eth_price).toLocaleString('fr-FR')}<br>
      SOL/USDT : $${Number(data.sol_price).toLocaleString('fr-FR')}
    `;

    // Solde + P&L
    document.getElementById('total_balance').textContent = Number(data.portfolio.total_balance).toLocaleString('fr-FR');
    const pnl = data.portfolio.unrealized_pnl;
    document.getElementById('pnl').innerHTML = pnl >= 0 
      ? `<span class="positive">+$${pnl.toLocaleString('fr-FR')}</span>` 
      : `<span class="negative">-$${Math.abs(pnl).toLocaleString('fr-FR')}</span>`;

    // Positions ouvertes
    let posHtml = '<p style="color:#888;">Aucune position ouverte pour le moment</p>';
    if (Object.keys(data.portfolio.positions).length > 0) {
      posHtml = '<ul>';
      for (let [sym, p] of Object.entries(data.portfolio.positions)) {
        if (p.amount > 0) posHtml += `<li><strong>${sym}</strong> : ${p.amount} @ $${p.entry_price}</li>`;
      }
      posHtml += '</ul>';
    }
    document.getElementById('positions').innerHTML = posHtml;

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
      </tr>`;
    });
    document.getElementById('signals').innerHTML = html || '<tr><td colspan="6" style="text-align:center;color:#666;">Aucun signal pour le moment</td></tr>';

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
    document.getElementById('history').innerHTML = hist || '<tr><td colspan="5" style="text-align:center;color:#666;">Aucun trade pour le moment</td></tr>';
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
