"""The VC Brain — Backend API (FastAPI).

Ejecutar con:  uvicorn api:app --reload --port 8000
El frontend React (Vite) consume estos endpoints vía proxy /api.
"""

import json

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from vcbrain.config import settings
from vcbrain.connect import generate_outreach, generate_rejection_note
from vcbrain.auth import current_user, issue_token, request_client_id, verify_credentials, verify_google_id_token
from vcbrain import db
from vcbrain.license_gate import verify_license
from vcbrain.models import FounderProfile
from vcbrain.openai_client import diagnose_openai_connectivity
from vcbrain.pipeline import refresh_decisions, run_maschmeyer_pipeline, run_pipeline
from vcbrain.profiles import analyze_public_profiles
from vcbrain.submissions import submit_startup
from vcbrain.thesis import DACH_COUNTRIES, MVP_SECTIONS, ROUND_SIZES
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
    verify_license()
    db.init_db()
    print(f"[vcbrain] Diagnóstico de red hacia OpenAI: {diagnose_openai_connectivity()}")


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
    status: str  # "approved" | "clear" (el rechazo pasa por /api/tickets/reject)


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


@app.get("/api/health/network")
def health_network():
    """Diagnóstico en vivo de la conectividad de este servidor hacia
    api.openai.com (DNS, HTTPS por IPv4 forzado, HTTPS por resolución
    default) — no gasta en llamadas reales de la API, solo prueba la
    conexión. Útil para aislar en qué capa falla exactamente en Railway."""
    return diagnose_openai_connectivity()


@app.get("/api/meta")
def meta(_: str = Depends(current_user)):
    """Catálogos del formulario de auto-registro (secciones, tamaños de
    ronda, países DACH) — la misma tesis que usa el Scout."""
    return {
        "sections": list(MVP_SECTIONS),
        "round_sizes": list(ROUND_SIZES),
        "countries": [{"name": name, "code": code} for name, code in DACH_COUNTRIES],
    }


@app.get("/api/auth/config")
def auth_config():
    """Config pública para inicializar el botón de Google en el frontend
    (el Client ID no es secreto, a diferencia del client secret)."""
    return {"google_client_id": settings.google_client_id}


@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    # Orden: (1) admin compartido, sin rol fijo — el frontend usa el rol
    # elegido antes del login; (2) cuenta fija de prueba "startup" (QA/demo);
    # (3) cuentas B2B registradas por código de invitación (rol fijo desde
    # el registro).
    client_id = request_client_id(request)
    if verify_credentials(req.username, req.password, client_id):
        return {
            "access_token": issue_token(req.username),
            "token_type": "bearer",
            "expires_in": settings.jwt_ttl_seconds,
            "role": None,
        }
    if verify_credentials(
        req.username, req.password, client_id, settings.startup_test_username, settings.startup_test_password
    ):
        return {
            "access_token": issue_token(req.username),
            "token_type": "bearer",
            "expires_in": settings.jwt_ttl_seconds,
            "role": "startup",
        }
    account = db.verify_account_password(req.username, req.password)
    if account is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos.")
    return {
        "access_token": issue_token(account["email"]),
        "token_type": "bearer",
        "expires_in": settings.jwt_ttl_seconds,
        "role": account["role"],
    }


class RegisterRequest(BaseModel):
    code: str
    email: str
    password: str
    name: str = ""


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    """Registro por código de invitación (ver /api/invites) — el código fija
    el rol (investor|startup) de la cuenta que se crea con él."""
    code = req.code.strip().upper()
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Email inválido.")
    if len(req.password) < 8:
        raise HTTPException(status_code=422, detail="La contraseña debe tener al menos 8 caracteres.")

    invite = db.get_invite_code(code)
    if invite is None:
        raise HTTPException(status_code=404, detail="Código de invitación no encontrado.")
    if invite["used_by"]:
        raise HTTPException(status_code=422, detail="Este código de invitación ya fue usado.")
    if db.get_account(email) is not None:
        raise HTTPException(status_code=422, detail="Ya existe una cuenta con ese email.")

    db.create_account(email=email, password=req.password, role=invite["role"], name=req.name.strip(), invite_code=code)
    db.mark_invite_used(code, email)
    return {
        "access_token": issue_token(email),
        "token_type": "bearer",
        "expires_in": settings.jwt_ttl_seconds,
        "role": invite["role"],
    }


class InviteRequest(BaseModel):
    role: str  # "investor" | "startup"
    note: str = ""


@app.post("/api/invites")
def create_invite(req: InviteRequest, user: str = Depends(current_user)):
    if req.role not in {"investor", "startup"}:
        raise HTTPException(status_code=422, detail="role debe ser 'investor' o 'startup'.")
    code = db.create_invite_code(role=req.role, note=req.note.strip(), created_by=user)
    return {"code": code}


@app.get("/api/invites")
def list_invites(_: str = Depends(current_user)):
    return {"invites": db.list_invite_codes()}


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
    """Tablero de tickets (aprobados / rechazados), persistido para que
    sobreviva a un reload. Incluye la nota de rechazo autogenerada, si hay."""
    return {"tickets": db.get_tickets(), "notes": db.get_ticket_notes()}


@app.post("/api/tickets")
def set_ticket(req: TicketRequest, _: str = Depends(current_user)):
    valid = {"approved", "clear"}  # el rechazo pasa por /api/tickets/reject
    if req.status not in valid:
        raise HTTPException(status_code=422, detail=f"status debe ser uno de: {', '.join(sorted(valid))}.")
    if not req.company.strip() or not req.name.strip():
        raise HTTPException(status_code=422, detail="company y name son obligatorios.")
    db.set_ticket_status(req.company.strip(), req.name.strip(), req.status)
    return {"ok": True}


class RejectTicketRequest(BaseModel):
    company: str
    name: str
    role: str = ""
    founder_score: int = 0
    justification: str = ""
    feedback: list[str] = []
    language: str = "en"


@app.post("/api/tickets/reject")
def reject_ticket(req: RejectTicketRequest, _: str = Depends(current_user)):
    """Rechaza en un solo paso: marca el ticket como rechazado y genera
    automáticamente una nota de feedback personalizada en el idioma
    seleccionado en el perfil (es/en/de)."""
    if not req.company.strip() or not req.name.strip():
        raise HTTPException(status_code=422, detail="company y name son obligatorios.")
    language = req.language if req.language in {"es", "en", "de"} else "en"
    founder = FounderProfile(
        name=req.name.strip(),
        company=req.company.strip(),
        role=req.role.strip(),
        founder_score=req.founder_score,
        justification=req.justification,
        feedback=req.feedback,
    )
    try:
        note, _provider = generate_rejection_note(founder, language)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    db.set_ticket_status(founder.company, founder.name, "rejected")
    db.save_ticket_note(founder.company, founder.name, note, language)
    return {"note": note}


def _submission_status(ticket_status: str | None) -> str:
    """El estatus que ve quien envió su startup no salta directo a
    aprobado/rechazado solo porque el motor ya lo decidió — espera a que el
    fondo lo revise en su tablero de tickets (mismo flujo que las startups
    encontradas por el Scout)."""
    if ticket_status == "approved":
        return "approved"
    if ticket_status == "rejected":
        return "rejected"
    return "submitted"


_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB por archivo


async def _read_upload(file: UploadFile | None) -> tuple[bytes, str, str] | None:
    if file is None or not file.filename:
        return None
    data = await file.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{file.filename}: máximo 15 MB por archivo.")
    return data, file.filename, file.content_type or "application/octet-stream"


@app.post("/api/submissions")
async def create_submission(
    user: str = Depends(current_user),
    company: str = Form(...),
    name: str = Form(...),
    role: str = Form(""),
    country: str = Form(...),
    website: str = Form(""),
    section: str = Form(""),
    round_size: str = Form(""),
    pitch: str = Form(""),
    extra_text: str = Form(""),
    video_url: str = Form(...),
    business_email: str = Form(""),
    linkedin: str = Form(""),
    instagram: str = Form(""),
    x_url: str = Form(""),
    team: str = Form("[]"),  # JSON: [{"name": "...", "role": "..."}]
    pdf: UploadFile | None = None,
):
    """Alta directa de una startup por su propio founder: mismo Judge/Score/
    Decide/Dedup que el Scout, sin búsqueda web — los campos son los mismos
    que pondera el Scout (equipo, redes sociales, email, pitch, video pitch,
    pitch deck en PDF)."""
    if not company.strip() or not name.strip():
        raise HTTPException(status_code=422, detail="company y name son obligatorios.")
    if country not in {"Germany", "Switzerland", "Austria"}:
        raise HTTPException(status_code=422, detail="country debe ser Germany, Switzerland o Austria.")
    if not video_url.strip():
        raise HTTPException(status_code=422, detail="El video pitch (URL) es obligatorio.")

    try:
        team_list = json.loads(team) if team else []
        if not isinstance(team_list, list):
            team_list = []
    except json.JSONDecodeError:
        team_list = []

    pdf_tuple = await _read_upload(pdf)

    founder = submit_startup(
        submitter=user,
        company=company.strip(),
        name=name.strip(),
        role=role.strip(),
        country=country,
        website=website.strip(),
        section=section.strip(),
        round_size=round_size.strip(),
        pitch=pitch.strip(),
        extra_text=extra_text.strip(),
        video_url=video_url.strip(),
        business_email=business_email.strip(),
        linkedin=linkedin.strip(),
        instagram=instagram.strip(),
        x_url=x_url.strip(),
        team=team_list,
        pdf=pdf_tuple,
    )
    return {"founder": founder.to_dict()}


@app.get("/api/submissions/mine")
def my_submissions(user: str = Depends(current_user)):
    """Para que quien envió su startup pueda ver el estatus: enviado → en
    progreso → aprobado/rechazado, con feedback si aplica."""
    rows = db.list_submissions(submitter=user)
    tickets = db.get_tickets()
    result = []
    for row in rows:
        founder = db.get_company_by_key(row["company_key"])
        founder = refresh_decisions({"founders": [founder]})["founders"][0] if founder else None
        result.append(
            {
                "company": row["company"],
                "name": row["name"],
                "created_at": row["created_at"],
                "status": _submission_status(tickets.get(row["founder_key"])),
                "founder": founder,
                "files": db.list_submission_files(row["id"]),
            }
        )
    return {"submissions": result}


@app.get("/api/submissions")
def all_submissions(_: str = Depends(current_user)):
    """Panel del fondo: todas las startups auto-enviadas, con los datos
    completos del founder — se revisan con el mismo semáforo/tickets que
    las encontradas por el Scout."""
    rows = db.list_submissions()
    founders = []
    for row in rows:
        f = db.get_company_by_key(row["company_key"])
        if f:
            founders.append(refresh_decisions({"founders": [f]})["founders"][0])
    return {"founders": founders}


@app.get("/api/submissions/files/{file_id}")
def get_submission_file(file_id: int, _: str = Depends(current_user)):
    """Sirve el PDF/imagen adjunto para verlo o descargarlo en el navegador."""
    record = db.get_submission_file(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    if record.get("url") and not record.get("data"):
        return {"url": record["url"]}
    data = bytes(record["data"]) if record["data"] is not None else b""
    return Response(
        content=data,
        media_type=record["content_type"],
        headers={"Content-Disposition": f'inline; filename="{record["filename"]}"'},
    )
