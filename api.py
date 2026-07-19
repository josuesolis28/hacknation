"""The VC Brain — Backend API (FastAPI).

Ejecutar con:  uvicorn api:app --reload --port 8000
El frontend React (Vite) consume estos endpoints vía proxy /api.
"""

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vcbrain.config import settings
from vcbrain.connect import generate_outreach
from vcbrain.auth import current_user, issue_token, request_client_id, verify_credentials
from vcbrain.models import FounderProfile
from vcbrain.pipeline import run_maschmeyer_pipeline, run_pipeline
from vcbrain.profiles import analyze_public_profiles
from vcbrain.translation import LANGUAGES, translate, translate_many

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


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileRequest(BaseModel):
    name: str
    company: str
    role: str = ""


class TranslationRequest(BaseModel):
    text: str
    language: str


class BatchTranslationRequest(BaseModel):
    texts: list[str]
    language: str


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
    language = settings.default_language if settings.default_language in LANGUAGES else "en"
    return {
        "ok": not missing,
        "missing_env": missing,
        "provider": settings.llm_provider,
        "default_language": language,
        "languages": list(LANGUAGES.keys()),
    }


@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    if not verify_credentials(req.username, req.password, request_client_id(request)):
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos.")
    return {"access_token": issue_token(req.username), "token_type": "bearer", "expires_in": settings.jwt_ttl_seconds}


@app.post("/api/scout")
def scout(req: ScoutRequest, _: str = Depends(current_user)):
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
def scout_maschmeyer(max_results: int | None = None, _: str = Depends(current_user)):
    """Arranca el sourcing completo de la tesis sin requerir una consulta manual."""
    missing = settings.validate()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Faltan variables de entorno: {', '.join(missing)}",
        )
    return run_maschmeyer_pipeline(max_results=max_results).to_dict()


@app.post("/api/outreach")
def outreach(req: OutreachRequest, _: str = Depends(current_user)):
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


@app.post("/api/profiles/analyze")
def analyze_profiles(req: ProfileRequest, _: str = Depends(current_user)):
    if not req.name.strip() or not req.company.strip():
        raise HTTPException(status_code=422, detail="Nombre y empresa son obligatorios.")
    return analyze_public_profiles(req.name.strip(), req.company.strip(), req.role.strip())


@app.post("/api/translate")
def translate_content(req: TranslationRequest, _: str = Depends(current_user)):
    if req.language not in LANGUAGES:
        raise HTTPException(status_code=422, detail="Idioma no soportado.")
    return {"text": translate(req.text, req.language), "language": req.language}


@app.post("/api/translate/batch")
def translate_batch(req: BatchTranslationRequest, _: str = Depends(current_user)):
    """Traduce varios textos en una sola llamada al modelo (una tarjeta = una
    llamada) en vez de una llamada por campo."""
    if req.language not in LANGUAGES:
        raise HTTPException(status_code=422, detail="Idioma no soportado.")
    translated = translate_many(tuple(req.texts), req.language)
    return {"texts": list(translated), "language": req.language}
