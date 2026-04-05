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

# Dashboard sophistiqué IBM Plex (propre et connecté)
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
      --bg-card2: #1a1a1a;
      --border: rgba(255,255,255,0.07);
      --border-md: rgba(255,255,255,0.12);
      --text-primary: #f0f0f0;
      --text-secondary: #888;
      --text-muted: #555;
      --green: #22c55e;
      --green-bg: rgba(34,197,94,0.1);
      --red: #ef4444;
      --red-bg: rgba(239,68,68,0.1);
      --font-mono: 'IBM Plex Mono', monospace;
      --font-sans: 'IBM Plex Sans', sans-serif;
      --radius: 8px;
      --radius-lg: 12px;
    }
    body { background: var(--bg); color: var(--text-primary); font-family: var(--font-sans); min-height: 100vh; }
    .wrapper { max-width: 1200px; margin: 0 auto; padding: 0 20px 40px; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 0.5px solid var(--border); position: sticky; top: 0; background: var(--bg); z-index: 100; }
    .logo { font-family: var(--font-mono); font-size: 15px; font-weight: 600; letter-spacing: -0.5px; }
    .live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
    .price-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; }
    @media(max-width:800px){ .price-grid { grid-template-columns: 1fr; } }
    .pcard { background: var(--bg-card); border: 0.5px solid var(--border); border-radius: var(--radius); padding: 16px; transition: border-color .2s; }
    .pcard:hover { border-color: var(--border-md); }
    .pcard-sym { font-family: var(--font-mono); font-size: 11px; font-weight: 600; color: var(--text-secondary); }
    .pcard-price { font-family: var(--font-mono); font-size: 22px; font-weight: 600; }
    .pill { display: inline-block; font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 3px; }
    .pill.buy { background: var(--green-bg); color: var(--green); }
    .pill.sell { background: var(--red-bg); color: var(--red); }
    .pill.hold { background: rgba(234,179,8,.1); color: #eab308; }
  </style>
</head>
<body>
<header>
  <div class="live-dot"></div>
  <span class="logo">CryptoBot</span>
  <span class="badge-live">LIVE</span>
</header>

<div class="wrapper">
  <div class="section-label">Prix en temps réel</div>
  <div class="price-grid" id="price-grid"></div>

  <div class="section-label" style="margin-top:32px">Derniers signaux</div>
  <div class="panel">
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr>
          <th style="text-align:left;padding:8px 0;color:var(--text-muted)">HEURE</th>
          <th style="text-align:left;padding:8px 0;color:var(--text-muted)">PAIRE</th>
          <th style="text-align:left;padding:8px 0;color:var(--text-muted)">SIGNAL</th>
          <th style="text-align:right;padding:8px 0;color:var(--text-muted)">RSI</th>
          <th style="text-align:left;padding:8px 0;color:var(--text-muted)">RAISON</th>
        </tr>
      </thead>
      <tbody id="signals-body"></tbody>
    </table>
  </div>
</div>

<script>
  async function updateDashboard() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();

      const grid = document.getElementById('price-grid');
      grid.innerHTML = `
        <div class="pcard"><div class="pcard-sym">BTC/USDT</div><div class="pcard-price">$${Number(data.btc_price).toLocaleString('fr-FR')}</div></div>
        <div class="pcard"><div class="pcard-sym">ETH/USDT</div><div class="pcard-price">$${Number(data.eth_price).toLocaleString('fr-FR')}</div></div>
        <div class="pcard"><div class="pcard-sym">SOL/USDT</div><div class="pcard-price">$${Number(data.sol_price).toLocaleString('fr-FR')}</div></div>
      `;

      const tbody = document.getElementById('signals-body');
      tbody.innerHTML = '';
      data.recent_signals.forEach(s => {
        const pill = s.signal === 'BUY' ? 'buy' : s.signal === 'SELL' ? 'sell' : 'hold';
        const row = document.createElement('tr');
        row.innerHTML = `
          <td style="padding:12px 0;color:var(--text-muted)">${new Date(s.timestamp*1000).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}</td>
          <td style="padding:12px 0;font-weight:600">${s.symbol}</td>
          <td style="padding:12px 0"><span class="pill ${pill}">${s.signal}</span></td>
          <td style="padding:12px 0;text-align:right">${s.rsi}</td>
          <td style="padding:12px 0;color:var(--text-muted)">${s.reason}</td>
        `;
        tbody.appendChild(row);
      });
    } catch(e) {}
  }

  setInterval(updateDashboard, 3000);
  updateDashboard();
</script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML_DASHBOARD)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/status")
async def status():
    try:
        return {
            "status": "online",
            "btc_price": get_price("BTC/USDT"),
            "eth_price": get_price("ETH/USDT"),
            "sol_price": get_price("SOL/USDT"),
            "recent_signals": [get_signal(sym) for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]],
            "timestamp": time.time()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
