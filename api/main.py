from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from bot.exchange import get_price
from bot.signals import get_signal
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
  <title>CryptoBot — Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0d0d0d;
      --bg-card: #141414;
      --border: rgba(255,255,255,0.1);
      --text: #f0f0f0;
      --muted: #888;
      --green: #22c55e;
      --red: #ef4444;
      --yellow: #eab308;
    }
    body { background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; min-height: 100vh; }
    .wrapper { max-width: 1200px; margin: 0 auto; padding: 20px; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 15px 20px; border-bottom: 1px solid var(--border); }
    .logo { font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 600; }
    .live { display: flex; align-items: center; gap: 8px; font-size: 14px; }
    .dot { width: 10px; height: 10px; background: var(--green); border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    .price-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin: 30px 0; }
    .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
    .symbol { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: var(--muted); }
    .price { font-family: 'IBM Plex Mono', monospace; font-size: 32px; font-weight: 600; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 16px 12px; text-align: left; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 500; font-size: 13px; }
    .pill { padding: 6px 16px; border-radius: 9999px; font-size: 13px; font-weight: 700; font-family: 'IBM Plex Mono', monospace; }
    .pill.buy { background: rgba(34,197,94,0.2); color: var(--green); }
    .pill.sell { background: rgba(239,68,68,0.2); color: var(--red); }
    .pill.hold { background: rgba(234,179,8,0.2); color: var(--yellow); }
    .score { font-weight: 700; color: var(--yellow); font-size: 15px; }
  </style>
</head>
<body>
<header>
  <div class="logo">CryptoBot</div>
  <div class="live"><div class="dot"></div>LIVE • EN TEMPS RÉEL</div>
</header>

<div class="wrapper">
  <h2>Prix en temps réel</h2>
  <div class="price-grid" id="price-grid"></div>

  <h2 style="margin: 40px 0 15px;">Derniers signaux</h2>
  <table>
    <thead>
      <tr>
        <th>HEURE</th>
        <th>PAIRE</th>
        <th>SIGNAL</th>
        <th>RSI</th>
        <th>SCORE</th>
        <th>RAISON</th>
      </tr>
    </thead>
    <tbody id="signals-body"></tbody>
  </table>
</div>

<script>
  async function update() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();

      const grid = document.getElementById('price-grid');
      grid.innerHTML = `
        <div class="card"><div class="symbol">BTC/USDT</div><div class="price">$${Number(data.btc_price).toLocaleString('fr-FR')}</div></div>
        <div class="card"><div class="symbol">ETH/USDT</div><div class="price">$${Number(data.eth_price).toLocaleString('fr-FR')}</div></div>
        <div class="card"><div class="symbol">SOL/USDT</div><div class="price">$${Number(data.sol_price).toLocaleString('fr-FR')}</div></div>
      `;

      const tbody = document.getElementById('signals-body');
      tbody.innerHTML = '';
      data.recent_signals.forEach(s => {
        const pill = s.signal === 'BUY' ? 'buy' : s.signal === 'SELL' ? 'sell' : 'hold';
        const row = document.createElement('tr');
        row.innerHTML = `
          <td style="color:var(--muted)">${new Date(s.timestamp*1000).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}</td>
          <td style="font-weight:600">${s.symbol}</td>
          <td><span class="pill ${pill}">${s.signal}</span></td>
          <td style="text-align:right">${s.rsi}</td>
          <td style="text-align:right"><span class="score">${s.score}/100</span></td>
          <td style="color:var(--muted)">${s.reason}</td>
        `;
        tbody.appendChild(row);
      });
    } catch(e) {}
  }
  setInterval(update, 3000);
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
    try:
        return {
            "status": "online",
            "btc_price": get_price("BTC/USDT"),
            "eth_price": get_price("ETH/USDT"),
            "sol_price": get_price("SOL/USDT"),
            "recent_signals": [{**get_signal(sym), "symbol": sym} for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]],
            "timestamp": time.time()
        }
    except:
        return {"status": "error", "btc_price": 0, "eth_price": 0, "sol_price": 0, "recent_signals": []}
