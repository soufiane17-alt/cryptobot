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
      --border: rgba(255,255,255,0.07);
      --text-primary: #f0f0f0;
      --text-secondary: #888;
      --text-muted: #555;
      --green: #22c55e;
      --red: #ef4444;
      --font-mono: 'IBM Plex Mono', monospace;
      --font-sans: 'IBM Plex Sans', sans-serif;
    }
    body { background: var(--bg); color: var(--text-primary); font-family: var(--font-sans); min-height: 100vh; }
    .wrapper { max-width: 1200px; margin: 0 auto; padding: 20px; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border); }
    .logo { font-family: var(--font-mono); font-size: 18px; font-weight: 600; }
    .live-dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    .price-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin: 24px 0; }
    .pcard { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
    .pcard-sym { font-family: var(--font-mono); font-size: 13px; color: var(--text-secondary); }
    .pcard-price { font-family: var(--font-mono); font-size: 28px; font-weight: 600; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 14px 12px; text-align: left; border-bottom: 1px solid var(--border); }
    th { color: var(--text-muted); font-weight: 500; font-size: 13px; }
    .pill { padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; font-family: var(--font-mono); }
    .pill.buy { background: rgba(34,197,94,0.15); color: var(--green); }
    .pill.sell { background: rgba(239,68,68,0.15); color: var(--red); }
    .pill.hold { background: rgba(234,179,8,0.15); color: #eab308; }
    .score { font-weight: 700; color: #eab308; }
  </style>
</head>
<body>
<header>
  <div class="live-dot"></div>
  <span class="logo">CryptoBot</span>
  <span>LIVE</span>
</header>

<div class="wrapper">
  <h2 style="margin-bottom:8px;">Prix en temps réel</h2>
  <div class="price-grid" id="price-grid"></div>

  <h2 style="margin:32px 0 12px;">Derniers signaux</h2>
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

      // Prix
      const grid = document.getElementById('price-grid');
      grid.innerHTML = `
        <div class="pcard">
          <div class="pcard-sym">BTC/USDT</div>
          <div class="pcard-price">$${Number(data.btc_price).toLocaleString('fr-FR')}</div>
        </div>
        <div class="pcard">
          <div class="pcard-sym">ETH/USDT</div>
          <div class="pcard-price">$${Number(data.eth_price).toLocaleString('fr-FR')}</div>
        </div>
        <div class="pcard">
          <div class="pcard-sym">SOL/USDT</div>
          <div class="pcard-price">$${Number(data.sol_price).toLocaleString('fr-FR')}</div>
        </div>
      `;

      // Tableau signaux
      const tbody = document.getElementById('signals-body');
      tbody.innerHTML = '';
      data.recent_signals.forEach(s => {
        const pillClass = s.signal === 'BUY' ? 'buy' : s.signal === 'SELL' ? 'sell' : 'hold';
        const row = document.createElement('tr');
        row.innerHTML = `
          <td style="color:var(--text-muted)">${new Date(s.timestamp*1000).toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'})}</td>
          <td style="font-weight:600">${s.symbol}</td>
          <td><span class="pill ${pillClass}">${s.signal}</span></td>
          <td style="text-align:right">${s.rsi}</td>
          <td style="text-align:right"><span class="score">${s.score}/100</span></td>
          <td style="color:var(--text-muted)">${s.reason}</td>
        `;
        tbody.appendChild(row);
      });
    } catch(e) { console.error(e); }
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
