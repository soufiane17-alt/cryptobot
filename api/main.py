from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="CryptoBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dashboard complet directement dans le code (plus de problème de fichier)
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CryptoBot Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', system-ui, sans-serif; }
        .live-dot { animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    </style>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen p-8">
    <div class="max-w-5xl mx-auto">
        <div class="flex items-center justify-between mb-10">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-emerald-500 rounded-2xl flex items-center justify-center text-3xl">🤖</div>
                <h1 class="text-4xl font-semibold">CryptoBot</h1>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <div class="w-3 h-3 bg-emerald-400 rounded-full live-dot"></div>
                <span class="font-medium">LIVE • EN TEMPS RÉEL</span>
            </div>
        </div>

        <div class="mb-10">
            <h2 class="text-zinc-400 text-sm mb-4">PRIX EN LIVE</h2>
            <div id="prices" class="grid grid-cols-3 gap-6"></div>
        </div>

        <div>
            <h2 class="text-zinc-400 text-sm mb-4">DERNIERS SIGNAUX</h2>
            <div id="signals" class="space-y-4"></div>
        </div>
    </div>

    <script>
        async function update() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                // Prix
                document.getElementById('prices').innerHTML = `
                    <div class="bg-zinc-900 rounded-3xl p-6 text-center">
                        <div class="text-zinc-400 text-xs">BTC/USDT</div>
                        <div class="text-4xl font-semibold text-emerald-400">$${data.btc_price}</div>
                    </div>
                    <div class="bg-zinc-900 rounded-3xl p-6 text-center">
                        <div class="text-zinc-400 text-xs">ETH/USDT</div>
                        <div class="text-4xl font-semibold text-emerald-400">$${data.eth_price}</div>
                    </div>
                    <div class="bg-zinc-900 rounded-3xl p-6 text-center">
                        <div class="text-zinc-400 text-xs">SOL/USDT</div>
                        <div class="text-4xl font-semibold text-emerald-400">$${data.sol_price}</div>
                    </div>
                `;

                // Signaux
                let html = '';
                data.recent_signals.forEach(s => {
                    const color = s.signal === 'BUY' ? 'text-emerald-400' : s.signal === 'SELL' ? 'text-red-400' : 'text-zinc-400';
                    html += `<div class="bg-zinc-900 rounded-3xl p-5 flex justify-between items-center">
                        <div><span class="${color} font-bold">${s.signal}</span> <span class="ml-3">${s.symbol}</span></div>
                        <div class="text-right"><div class="text-sm">RSI ${s.rsi}</div><div class="text-xs text-zinc-500">${s.reason}</div></div>
                    </div>`;
                });
                document.getElementById('signals').innerHTML = html || '<p class="text-zinc-500">Aucun signal pour le moment</p>';
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

@app.get("/health")
async def health():
    return {"status": "ok", "service": "CryptoBot API"}

@app.get("/api/status")
async def status():
    # Tu peux garder ton code actuel ici, ou le laisser tel quel
    return {"status": "online", "btc_price": 67100, "eth_price": 2050, "sol_price": 80, "recent_signals": []}

print("✅ Dashboard inline prêt (version stable)")
