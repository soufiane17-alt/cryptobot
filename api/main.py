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

# HTML minimal et propre directement dans le code
HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CryptoBot Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: system-ui; background: #0a0a0a; color: white; padding: 40px; text-align: center; }
        .live { animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }
    </style>
</head>
<body>
    <h1 class="text-5xl font-bold mb-4">🚀 CryptoBot</h1>
    <p class="text-emerald-400 text-xl">✅ Dashboard chargé avec succès</p>
    <p class="mt-8 text-zinc-400">Si tu vois ce message, tout fonctionne.</p>
    
    <div id="data" class="mt-12 bg-zinc-900 p-6 rounded-2xl inline-block text-left"></div>

    <script>
        fetch('/api/status')
            .then(r => r.json())
            .then(d => {
                document.getElementById('data').innerHTML = `
                    BTC : $${d.btc_price}<br>
                    ETH : $${d.eth_price}<br>
                    SOL : $${d.sol_price}
                `;
            });
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/status")
async def status():
    return {"status": "online", "btc_price": 67100, "eth_price": 2050, "sol_price": 80, "recent_signals": []}

print("✅ Dashboard inline prêt")
