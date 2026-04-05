from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

app = FastAPI(title="CryptoBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage conditionnel des fichiers statiques (solution pro)
static_dir = Path("frontend/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    print("⚠️ Dossier frontend/static non trouvé → dashboard accessible mais sans fichiers statiques supplémentaires")

# Importer les routes
from api.routes.dashboard import router as dashboard_router
app.include_router(dashboard_router)

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "CryptoBot API"}

print("✅ FastAPI + Dashboard prêt (version pro)")
