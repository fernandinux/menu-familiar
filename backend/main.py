"""
Backend FastAPI — Menú Familiar Paca
Desplegado en Render.com (free tier)

Lee y escribe datos en el repositorio GitHub via GitHub API (PyGithub).
Así los datos persisten aunque Render duerma o se reinicie.

Variables de entorno requeridas (configurar en Render):
  GITHUB_TOKEN  — Personal Access Token con permisos repo (read/write)
  GITHUB_REPO   — nombre del repo, ej: "fernando-paca/menu-familiar"
  GEMINI_API_KEY — (para GitHub Actions, no usado aquí directamente)
"""

import os
import json
import base64
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github, GithubException

# ── CONFIG ────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("menu-paca")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")   # ej: "fernando-paca/menu-familiar"
BRANCH       = os.getenv("GITHUB_BRANCH", "main")

DATA_MENU_PATH      = "data/menu_actual.json"
DATA_FEEDBACKS_PATH = "data/feedbacks.json"
DATA_LONCHERA_PATH  = "data/lonchera.json"

app = FastAPI(
    title="Menú Familiar Paca",
    description="API para el sistema de menú semanal de la Familia Paca",
    version="1.1.0",
)

# CORS — permite peticiones desde Netlify (y localhost para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── GITHUB HELPER ─────────────────────────────────────────────
def get_repo():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise HTTPException(
            status_code=503,
            detail="GitHub no configurado. Revisa GITHUB_TOKEN y GITHUB_REPO en Render."
        )
    g = Github(GITHUB_TOKEN)
    try:
        return g.get_repo(GITHUB_REPO)
    except GithubException as e:
        logger.error(f"GitHub repo error: {e}")
        raise HTTPException(status_code=503, detail=f"No se pudo acceder al repo: {e.data.get('message', str(e))}")


def read_json_from_github(path: str) -> dict | list:
    """Lee un archivo JSON del repo GitHub."""
    repo = get_repo()
    try:
        contents = repo.get_contents(path, ref=BRANCH)
        raw = base64.b64decode(contents.content).decode("utf-8")
        return json.loads(raw)
    except GithubException as e:
        if e.status == 404:
            return None
        raise HTTPException(status_code=502, detail=f"Error leyendo {path}: {e.data.get('message', str(e))}")


def write_json_to_github(path: str, data: dict | list, commit_msg: str):
    """Escribe un archivo JSON en el repo GitHub (crea o actualiza)."""
    repo = get_repo()
    content = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = content.encode("utf-8")

    try:
        existing = repo.get_contents(path, ref=BRANCH)
        repo.update_file(
            path=path,
            message=commit_msg,
            content=encoded,
            sha=existing.sha,
            branch=BRANCH,
        )
    except GithubException as e:
        if e.status == 404:
            repo.create_file(
                path=path,
                message=commit_msg,
                content=encoded,
                branch=BRANCH,
            )
        else:
            raise HTTPException(status_code=502, detail=f"Error escribiendo {path}: {e.data.get('message', str(e))}")


def write_text_to_github(path: str, text: str, commit_msg: str):
    """Escribe texto plano en el repo GitHub (crea o actualiza)."""
    repo = get_repo()
    encoded = text.encode("utf-8")
    try:
        existing = repo.get_contents(path, ref=BRANCH)
        repo.update_file(path=path, message=commit_msg, content=encoded, sha=existing.sha, branch=BRANCH)
    except GithubException as e:
        if e.status == 404:
            repo.create_file(path=path, message=commit_msg, content=encoded, branch=BRANCH)
        else:
            raise HTTPException(status_code=502, detail=f"Error escribiendo {path}: {e.data.get('message', str(e))}")


# ── MODELOS ───────────────────────────────────────────────────
class FeedbackIn(BaseModel):
    quien: str
    tipos: List[str]
    plato: Optional[str] = None
    ingrediente: Optional[str] = None
    cantidad: Optional[str] = None
    comentario: Optional[str] = None

class LoncheraIn(BaseModel):
    texto: str   # texto libre tal como lo escribe Fernando


# ── ENDPOINTS ─────────────────────────────────────────────────

@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "app": "Menu Familiar Paca", "version": "1.1.0"}


@app.get("/menu-actual", summary="Devuelve el menú de la semana actual")
def menu_actual():
    data = read_json_from_github(DATA_MENU_PATH)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Menú no disponible todavía. Será generado el próximo sábado automáticamente."
        )
    return data


@app.get("/menu-anterior", summary="Devuelve el menú de la semana anterior")
def menu_anterior():
    data = read_json_from_github("data/menu_anterior.json")
    if data is None:
        raise HTTPException(status_code=404, detail="Aún no hay menú anterior guardado.")
    return data


@app.post("/feedback", summary="Guarda un feedback de la familia", status_code=201)
def guardar_feedback(fb: FeedbackIn):
    existing = read_json_from_github(DATA_FEEDBACKS_PATH)
    if existing is None:
        existing = []

    nuevo = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "quien": fb.quien,
        "tipos": fb.tipos,
        "plato": fb.plato,
        "ingrediente": fb.ingrediente,
        "cantidad": fb.cantidad,
        "comentario": fb.comentario,
    }
    existing.append(nuevo)

    write_json_to_github(
        path=DATA_FEEDBACKS_PATH,
        data=existing,
        commit_msg=f"feedback: {fb.quien} — {', '.join(fb.tipos)}"
    )
    logger.info(f"Feedback guardado: {fb.quien} → {fb.tipos}")
    return {"ok": True, "mensaje": "Feedback guardado correctamente"}


@app.get("/feedbacks", summary="Devuelve todos los feedbacks guardados")
def listar_feedbacks():
    data = read_json_from_github(DATA_FEEDBACKS_PATH)
    if data is None:
        return []
    return data


# ── LONCHERA ──────────────────────────────────────────────────

@app.get("/lonchera", summary="Devuelve la lonchera del mes actual")
def get_lonchera():
    """
    Devuelve el JSON de lonchera almacenado en data/lonchera.json.
    Contiene la asignación fija de lonchera por día para Facundo y Leonardo.
    """
    data = read_json_from_github(DATA_LONCHERA_PATH)
    if data is None:
        raise HTTPException(status_code=404, detail="No hay lonchera configurada aún.")
    return data


@app.post("/lonchera", summary="Actualiza la lonchera del mes", status_code=200)
def actualizar_lonchera(body: LoncheraIn):
    """
    Recibe texto libre con la nueva asignación de lonchera y lo guarda
    en data/lonchera.json como campo 'texto_libre' junto con la fecha.
    Fernando puede escribir la lonchera en el formato que quiera.
    """
    if not body.texto or not body.texto.strip():
        raise HTTPException(status_code=400, detail="El texto de lonchera no puede estar vacío.")

    data = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "texto_libre": body.texto.strip()
    }

    write_json_to_github(
        path=DATA_LONCHERA_PATH,
        data=data,
        commit_msg=f"lonchera: actualización {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )
    logger.info("Lonchera actualizada")
    return {"ok": True, "mensaje": "Lonchera actualizada correctamente"}


@app.delete("/feedbacks", summary="Limpia los feedbacks (solo tras generar menú)", include_in_schema=False)
def limpiar_feedbacks():
    write_json_to_github(
        path=DATA_FEEDBACKS_PATH,
        data=[],
        commit_msg="chore: limpiar feedbacks tras generación de menú"
    )
    return {"ok": True}
