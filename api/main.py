from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="CryptoBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Importer les routes du dashboard
from api.routes.dashboard import router as dashboard_router
app.include_router(dashboard_router)

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "CryptoBot API"}

print("✅ Dashboard + API prêt !")
