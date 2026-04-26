"""
Backend FastAPI — Menú Familiar Paca v2
Render.com (free tier)
"""

import os, json, base64, logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github, GithubException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("menu-paca")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")
BRANCH       = os.getenv("GITHUB_BRANCH", "main")

app = FastAPI(title="Menú Familiar Paca", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_repo():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise HTTPException(503, "GitHub no configurado. Revisa GITHUB_TOKEN y GITHUB_REPO en Render.")
    try:
        return Github(GITHUB_TOKEN).get_repo(GITHUB_REPO)
    except GithubException as e:
        raise HTTPException(503, f"No se pudo acceder al repo: {e.data.get('message', str(e))}")

def read_json(path: str):
    repo = get_repo()
    try:
        contents = repo.get_contents(path, ref=BRANCH)
        return json.loads(base64.b64decode(contents.content).decode("utf-8"))
    except GithubException as e:
        if e.status == 404:
            return None
        raise HTTPException(502, f"Error leyendo {path}: {e.data.get('message', str(e))}")

def write_json(path: str, data, commit_msg: str):
    repo = get_repo()
    encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    try:
        existing = repo.get_contents(path, ref=BRANCH)
        repo.update_file(path=path, message=commit_msg, content=encoded, sha=existing.sha, branch=BRANCH)
    except GithubException as e:
        if e.status == 404:
            repo.create_file(path=path, message=commit_msg, content=encoded, branch=BRANCH)
        else:
            raise HTTPException(502, f"Error escribiendo {path}: {e.data.get('message', str(e))}")

# ── MODELOS ───────────────────────────────────────────────────
class FeedbackIn(BaseModel):
    quien: str
    tipos: List[str]
    plato: Optional[str] = None
    ingrediente: Optional[str] = None
    cantidad: Optional[str] = None
    comentario: Optional[str] = None

class LoncheraIn(BaseModel):
    texto: str

# ── ENDPOINTS ─────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "app": "Menu Familiar Paca", "version": "2.0.0"}

@app.get("/menu-actual")
def menu_actual():
    data = read_json("data/menu_actual.json")
    if data is None:
        raise HTTPException(404, "Menú no disponible. Será generado el próximo sábado.")
    return data

@app.get("/menu-anterior")
def menu_anterior():
    data = read_json("data/menu_anterior.json")
    if data is None:
        raise HTTPException(404, "Aún no hay menú anterior guardado.")
    return data

@app.post("/feedback", status_code=201)
def guardar_feedback(fb: FeedbackIn):
    existing = read_json("data/feedbacks.json") or []
    existing.append({
        "fecha": datetime.now(timezone.utc).isoformat(),
        "quien": fb.quien,
        "tipos": fb.tipos,
        "plato": fb.plato,
        "ingrediente": fb.ingrediente,
        "cantidad": fb.cantidad,
        "comentario": fb.comentario,
    })
    write_json("data/feedbacks.json", existing, f"feedback: {fb.quien} — {', '.join(fb.tipos)}")
    return {"ok": True, "mensaje": "Feedback guardado correctamente"}

@app.get("/feedbacks")
def listar_feedbacks():
    return read_json("data/feedbacks.json") or []

@app.get("/lonchera")
def get_lonchera():
    data = read_json("data/lonchera.json")
    if data is None:
        raise HTTPException(404, "No hay lonchera configurada.")
    return data

@app.post("/lonchera")
def actualizar_lonchera(body: LoncheraIn):
    if not body.texto or not body.texto.strip():
        raise HTTPException(400, "El texto de lonchera no puede estar vacío.")
    data = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "texto_libre": body.texto.strip()
    }
    write_json("data/lonchera.json", data, f"lonchera: actualización {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    return {"ok": True, "mensaje": "Lonchera actualizada correctamente"}

@app.get("/memoria")
def get_memoria():
    """Devuelve la memoria permanente de preferencias de la familia."""
    data = read_json("data/memoria.json")
    if data is None:
        return {"reglas_permanentes": [], "historial_feedbacks": []}
    return data

@app.delete("/feedbacks", include_in_schema=False)
def limpiar_feedbacks():
    write_json("data/feedbacks.json", [], "chore: limpiar feedbacks")
    return {"ok": True}
