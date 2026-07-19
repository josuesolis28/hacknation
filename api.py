"""The VC Brain — Backend API (FastAPI).

Ejecutar con:  uvicorn api:app --reload --port 8000
El frontend React (Vite) consume estos endpoints vía proxy /api.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vcbrain.config import settings
from vcbrain.connect import generate_outreach
from vcbrain.models import FounderProfile
from vcbrain.pipeline import run_maschmeyer_pipeline, run_pipeline

app = FastAPI(title="The VC Brain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoutRequest(BaseModel):
    query: str
    max_results: int | None = None


class OutreachRequest(BaseModel):
    name: str
    company: str
    role: str = ""
    signals: list[str] = []
    justification: str = ""
    evidence: list[str] = []


@app.get("/api/health")
def health():
    missing = settings.validate()
    return {"ok": not missing, "missing_env": missing, "provider": settings.llm_provider}


@app.post("/api/scout")
def scout(req: ScoutRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="La búsqueda no puede estar vacía.")
    missing = settings.validate()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Faltan variables de entorno: {', '.join(missing)}",
        )
    result = run_pipeline(query, max_results=req.max_results)
    return result.to_dict()


@app.post("/api/scout/maschmeyer")
def scout_maschmeyer(max_results: int | None = None):
    """Arranca el sourcing completo de la tesis sin requerir una consulta manual."""
    missing = settings.validate()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Faltan variables de entorno: {', '.join(missing)}",
        )
    return run_maschmeyer_pipeline(max_results=max_results).to_dict()


@app.post("/api/outreach")
def outreach(req: OutreachRequest):
    founder = FounderProfile(
        name=req.name,
        company=req.company,
        role=req.role,
        founder_score=0,
        justification=req.justification,
        signals=req.signals,
        evidence=req.evidence,
    )
    try:
        message, provider = generate_outreach(founder)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"message": message, "provider": provider}
