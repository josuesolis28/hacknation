"""The VC Brain — Backend API (FastAPI).

Ejecutar con:  uvicorn api:app --reload --port 8000
El frontend React (Vite) consume estos endpoints vía proxy /api.
"""

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vcbrain.config import settings
from vcbrain.connect import generate_outreach
from vcbrain.auth import current_user, issue_token, request_client_id, verify_credentials, verify_google_id_token
from vcbrain import db
from vcbrain.models import FounderProfile
from vcbrain.pipeline import refresh_decisions, run_maschmeyer_pipeline, run_pipeline
from vcbrain.profiles import analyze_public_profiles
from vcbrain.translation import LANGUAGES, translate, translate_many

app = FastAPI(title="The VC Brain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


class ScoutRequest(BaseModel):
    query: str
    max_results: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str  # ID token que devuelve el botón "Sign in with Google"


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


class DecisionRequest(BaseModel):
    company: str
    name: str
    state: str  # "forced" | "discarded" | "clear"


class TicketRequest(BaseModel):
    company: str
    name: str
    status: str  # "approved" | "rejected" | "follow_up" | "completed" | "clear"


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


@app.get("/api/auth/config")
def auth_config():
    """Config pública para inicializar el botón de Google en el frontend
    (el Client ID no es secreto, a diferencia del client secret)."""
    return {"google_client_id": settings.google_client_id}


@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    if not verify_credentials(req.username, req.password, request_client_id(request)):
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos.")
    return {"access_token": issue_token(req.username), "token_type": "bearer", "expires_in": settings.jwt_ttl_seconds}


@app.post("/api/auth/google")
def login_google(req: GoogleLoginRequest):
    claims = verify_google_id_token(req.credential)
    email = str(claims.get("email", ""))
    db.upsert_google_user(
        google_sub=str(claims.get("sub", "")),
        email=email,
        name=str(claims.get("name", "")),
        picture=str(claims.get("picture", "")),
    )
    return {"access_token": issue_token(email), "token_type": "bearer", "expires_in": settings.jwt_ttl_seconds}


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
    db.save_scan(result)
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
    result = run_maschmeyer_pipeline(max_results=max_results)
    db.save_scan(result)
    return result.to_dict()


@app.get("/api/scout/latest")
def scout_latest(_: str = Depends(current_user)):
    """Devuelve el último escaneo guardado, si existe — evita volver a pagar
    el costo de una corrida completa solo por refrescar el navegador.

    Las decisiones se recalculan con la regla vigente antes de devolver el
    resultado: si la regla de negocio cambió después de guardar esta corrida
    (p. ej. el umbral de aprobación), un resultado cacheado no debe seguir
    mostrando una decisión calculada con la regla vieja."""
    result = db.get_latest_scan()
    return {"result": refresh_decisions(result) if result else None}


@app.get("/api/companies")
def list_companies(_: str = Depends(current_user)):
    """Todas las startups ya monitoreadas alguna vez (deduplicadas), para la
    sección "ya analizadas" — no requiere volver a escanear para verlas."""
    companies = db.list_companies()
    for c in companies:
        c["founder"] = refresh_decisions({"founders": [c["founder"]]})["founders"][0]
    return {"companies": companies}


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


@app.get("/api/decisions")
def list_decisions(_: str = Depends(current_user)):
    """Anulaciones manuales (aprobar amarillo a la fuerza / descartar), \
persistidas para que sobrevivan a un reload."""
    return {"decisions": db.get_decisions()}


@app.post("/api/decisions")
def set_decision(req: DecisionRequest, _: str = Depends(current_user)):
    if req.state not in {"forced", "discarded", "clear"}:
        raise HTTPException(status_code=422, detail="state debe ser 'forced', 'discarded' o 'clear'.")
    if not req.company.strip() or not req.name.strip():
        raise HTTPException(status_code=422, detail="company y name son obligatorios.")
    db.set_decision(req.company.strip(), req.name.strip(), req.state)
    return {"ok": True}


@app.get("/api/tickets")
def list_tickets(_: str = Depends(current_user)):
    """Tablero de tickets (aprobados / rechazados / en seguimiento / \
completados), persistido para que sobreviva a un reload."""
    return {"tickets": db.get_tickets()}


@app.post("/api/tickets")
def set_ticket(req: TicketRequest, _: str = Depends(current_user)):
    valid = {"approved", "rejected", "follow_up", "completed", "clear"}
    if req.status not in valid:
        raise HTTPException(status_code=422, detail=f"status debe ser uno de: {', '.join(sorted(valid))}.")
    if not req.company.strip() or not req.name.strip():
        raise HTTPException(status_code=422, detail="company y name son obligatorios.")
    db.set_ticket_status(req.company.strip(), req.name.strip(), req.status)
    return {"ok": True}
