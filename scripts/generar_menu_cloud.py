"""
GENERADOR DE MENÚ SEMANAL — versión CLOUD
Familia Paca, Lima Perú

Ejecutado automáticamente por GitHub Actions cada sábado a las 12:00 UTC (7am Lima).
Escribe el resultado en data/menu_actual.json del repo.

Variables de entorno requeridas:
  GEMINI_API_KEY   — clave de Google Gemini
  GITHUB_TOKEN     — PAT para escribir en el repo
  GITHUB_REPO      — ej: "fernando-paca/menu-familiar"
  GITHUB_BRANCH    — rama (default: main)
"""

import json
import os
import ssl
import sys
import base64
from datetime import datetime, timedelta
from pathlib import Path

# ── SSL (Linux/Actions no tiene este problema, pero por si acaso) ──
try:
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    ssl_context = ssl.create_default_context()

# ── CONFIG ────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO    = os.environ.get("GITHUB_REPO", "")
BRANCH         = os.environ.get("GITHUB_BRANCH", "main")

DATA_MENU_PATH      = "data/menu_actual.json"
DATA_FEEDBACKS_PATH = "data/feedbacks.json"
DATA_HISTORIAL_PATH = "data/historial.json"
DATA_MENU_ANTERIOR  = "data/menu_anterior.json"   # ← agregar esta línea
# ── PROMPT MAESTRO ────────────────────────────────────────────
PROMPT_SISTEMA = """
Eres un nutricionista especializado en familias con necesidades dietéticas específicas en Lima, Perú.
Tu tarea es generar el plan de desayunos y almuerzos de la semana para la familia Paca.

## FAMILIA
- Fernando (padre, adulto): tiene RESISTENCIA A LA INSULINA — debe controlar carbohidratos
- Lourdes (madre, adulta): sin restricciones específicas
- Facundo (hijo, 4 años): tiene TRASTORNO DEL ESPECTRO AUTISTA (TEA) nivel 1 — ver reglas especiales
- Leonardo (hijo, 2 años): en etapa de desarrollo, necesita máxima variedad de nutrientes
- Roxana (cocinera, adulta): sin restricciones
- Luna (nana, adulta): sin restricciones
TOTAL: 6 personas (4 adultos + 2 niños pequeños)

## REGLA FUNDAMENTAL — UN SOLO MENÚ PARA TODOS
Todos comen lo mismo. NO se preparan platos separados. El menú debe ser apto para adultos Y para niños de 2 y 4 años al mismo tiempo.

## REGLAS PARA FACUNDO (TEA nivel 1)
EVITAR SIEMPRE:
- Colorantes artificiales, conservantes artificiales, azúcar refinada en exceso
- Glutamato monosódico (MSG/ajinomoto) en exceso
- Alimentos ultraprocesados, grasas trans
FAVORECER SIEMPRE:
- Alimentos fermentados naturales: yogur natural sin azúcar, queso fresco
- Fibra soluble: avena, lentejas, arvejas, zanahorias, plátano
- Omega-3: pescado (bonito, jurel, caballa, atún en agua), huevo de corral
- Vitaminas B6, B12, C, D y zinc
- Probióticos naturales: yogur natural, queso fresco

## REGLAS PARA FERNANDO (Resistencia a la insulina)
- Reducir carbohidratos refinados
- Arroz, papa, camote en PORCIONES MODERADAS
- Priorizar: proteínas magras, palta, aceite de oliva, pecanas, nueces
- Desayunos preferentemente sin pan o con pan integral en pequeña cantidad

## REGLAS GENERALES
- Cada desayuno: proteína + fruta o vegetal + carbohidrato opcional (integral)
- Cada almuerzo: proteína principal + vegetal + carbohidrato moderado
- Variedad de colores (mínimo 3 por almuerzo)
- Pescado al menos 2 veces por semana
- Legumbres al menos 1-2 veces por semana
- Vegetales no criollos al menos 3 veces: brócoli, zucchini, berenjena, espinaca, pimientos, coliflor
- El domingo el almuerzo debe ser SENCILLO DE PREPARAR o que resista bien el recalentamiento

## INGREDIENTES DISPONIBLES EN LIMA, PERÚ
Proteínas: pollo, res, cerdo, bonito, jurel, caballa, pejerrey, lenguado, corvina, atún en conserva, sardinas, choros, huevos, lentejas, frijoles canarios, pallares, arvejas, garbanzos
Vegetales: tomate, cebolla, ajo, zanahoria, papa, camote, yuca, choclo, vainita, betarraga, pepino, poro, brócoli, coliflor, espinaca, acelga, zucchini, berenjena, pimiento (rojo/verde/amarillo), apio, lechuga, albahaca, perejil, culantro
Frutas: plátano, papaya, mango, mandarina, naranja, limón, palta, fresa, maracuyá, granadilla, chirimoya, manzana, pera
Lácteos: leche evaporada, leche fresca, yogur natural, queso fresco, queso edam
Granos: arroz, fideos, pan de molde integral, avena, quinua, kiwicha
Especias: orégano, comino, ají amarillo, ají panca, ají limo, rocoto, culantro, perejil

REGLAS PARA LAS CANTIDADES:
- Carnes y pescados: 200-250g por adulto y 100-120g por niño = aprox. 1kg a 1.2kg para 6 personas
- Huevos: indicar cantidad exacta de unidades
- Arroz: máximo 2 tazas para los 6
- El domingo solo comen 4 personas (Fernando, Lourdes, Facundo, Leonardo)

## FORMATO DE SALIDA — JSON EXACTO
Devuelve ÚNICAMENTE el JSON, sin texto antes ni después:
{
  "semana": "Lunes DD/MM al Domingo DD/MM/AAAA",
  "dias": {
    "lunes": {
      "desayuno": {
        "nombre": "Nombre del plato",
        "descripcion": "Preparación en 1 línea corta",
        "ingredientes_principales": ["ingrediente1 - cantidad para 6", "ingrediente2 - cantidad"],
        "nota_facundo": "beneficio clave para Facundo (1 línea)",
        "nota_fernando": "adaptación para RI (1 línea)"
      },
      "almuerzo": {
        "nombre": "Nombre del plato",
        "descripcion": "Preparación en 1 línea corta",
        "ingredientes_principales": ["ingrediente1 - cantidad para 6"],
        "nota_facundo": "beneficio clave para Facundo",
        "nota_fernando": "adaptación para RI"
      }
    },
    "martes": {},
    "miercoles": {},
    "jueves": {},
    "viernes": {},
    "sabado": {},
    "domingo": {
      "desayuno": {},
      "almuerzo": {
        "nombre": "",
        "descripcion": "",
        "ingredientes_principales": [],
        "nota_facundo": "",
        "nota_fernando": "",
        "nota_domingo": "por qué es sencillo o resiste recalentamiento"
      }
    }
  },
  "lista_compras_domingos": {
    "descripcion": "Compra dominical para lunes, martes, miercoles",
    "carnes_y_proteinas": ["item - cantidad"],
    "vegetales_y_frutas": ["item - cantidad"],
    "lacteos_y_huevos": ["item - cantidad"],
    "despensa": ["item - cantidad"]
  },
  "lista_compras_mitad_semana": {
    "descripcion": "Compra de mitad de semana para jueves, viernes, sabado, domingo",
    "carnes_y_proteinas": ["item - cantidad"],
    "vegetales_y_frutas": ["item - cantidad"],
    "lacteos_y_huevos": ["item - cantidad"],
    "despensa": ["item - cantidad"]
  }
}
"""


def construir_prompt(fecha_inicio: str, historial: list, feedbacks: list) -> str:
    """Construye el prompt completo con historial y feedbacks."""
    
    # Historial: evitar repetir platos
    historial_texto = ""
    if historial:
        platos_previos = []
        for semana in historial[-3:]:
            platos_previos.extend(semana.get("platos_usados", []))
        if platos_previos:
            historial_texto = f"""
## PLATOS USADOS EN LAS ÚLTIMAS 3 SEMANAS (NO REPETIR)
{chr(10).join(f"- {p}" for p in platos_previos)}
"""

    # Feedbacks de la familia
    feedbacks_texto = ""
    if feedbacks:
        fb_lines = []
        for fb in feedbacks[-20:]:  # Max últimos 20
            quien = fb.get("quien", "")
            tipos = ", ".join(fb.get("tipos", []))
            comentario = fb.get("comentario", "")
            plato = fb.get("plato", "")
            ingrediente = fb.get("ingrediente", "")
            cantidad = fb.get("cantidad", "")
            
            line = f"- {quien} [{tipos}]"
            if plato:
                line += f" sobre '{plato.split('|')[-1] if '|' in plato else plato}'"
            if ingrediente:
                line += f": ingrediente difícil = {ingrediente}"
            if cantidad:
                line += f": cantidad = {cantidad}"
            if comentario:
                line += f": {comentario}"
            fb_lines.append(line)
        
        if fb_lines:
            feedbacks_texto = f"""
## FEEDBACK DE LA FAMILIA DE LA SEMANA PASADA (INCORPORAR EN ESTE MENÚ)
La familia ha dado el siguiente feedback. Por favor, tenlo en cuenta al planificar:
{chr(10).join(fb_lines)}
"""

    prompt = f"""
Genera el plan completo de desayunos y almuerzos para la semana que comienza el {fecha_inicio}.
{historial_texto}
{feedbacks_texto}

Recuerda:
- Incluir al menos 2 platos con pescado durante la semana
- Al menos 3 desayunos con proteína alta (huevos, atún, queso)
- Al menos 3 almuerzos con vegetales no criollos (brócoli, zucchini, berenjena, pimiento de colores)
- El almuerzo del domingo debe ser sencillo o resistir bien el recalentamiento
- Todas las cantidades correctas para 6 personas (excepto almuerzo dominical: 4 personas)
- Devuelve ÚNICAMENTE el JSON, sin texto adicional
"""
    return prompt


def llamar_gemini(prompt_usuario: str) -> dict:
    """Llama a la API de Gemini 2.5 Flash y devuelve el JSON del plan."""
    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "system_instruction": {"parts": [{"text": PROMPT_SISTEMA}]},
        "contents": [{"parts": [{"text": prompt_usuario}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 65536,
            "responseMimeType": "application/json",
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl_context) as response:
            result = json.loads(response.read().decode("utf-8"))

            finish_reason = result.get("candidates", [{}])[0].get("finishReason", "")
            if finish_reason == "MAX_TOKENS":
                raise Exception("Respuesta cortada por límite de tokens. Re-ejecutar.")

            texto = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if texto.startswith("```json"):
                texto = texto[7:]
            elif texto.startswith("```"):
                texto = texto.split("\n", 1)[1]
            if texto.endswith("```"):
                texto = texto.rsplit("```", 1)[0]

            return json.loads(texto.strip())

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"Error API Gemini ({e.code}): {error_body}")


# ── GITHUB I/O ────────────────────────────────────────────────
def _gh_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _gh_get(path: str):
    import urllib.request, urllib.error
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}?ref={BRANCH}"
    req = urllib.request.Request(url, headers=_gh_headers())
    try:
        with urllib.request.urlopen(req, context=ssl_context) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.status == 404:
            return None
        raise


def _gh_put(path: str, content_str: str, message: str, sha: str = None):
    import urllib.request
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_gh_headers(), method="PUT")
    with urllib.request.urlopen(req, context=ssl_context) as r:
        return json.loads(r.read().decode())


def leer_json_github(path: str):
    item = _gh_get(path)
    if item is None:
        return None, None
    raw = base64.b64decode(item["content"]).decode("utf-8")
    return json.loads(raw), item["sha"]


def escribir_json_github(path: str, data, message: str, sha: str = None):
    content_str = json.dumps(data, ensure_ascii=False, indent=2)
    _gh_put(path, content_str, message, sha)
    print(f"  ✅ {path} actualizado en GitHub")


# ── MAIN ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🍽️  GENERADOR DE MENÚ — FAMILIA PACA (CLOUD)")
    print("=" * 60)

    # Validaciones
    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY no configurada")
        sys.exit(1)
    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN no configurado")
        sys.exit(1)
    if not GITHUB_REPO:
        print("❌ ERROR: GITHUB_REPO no configurado")
        sys.exit(1)

    # Calcular semana PRÓXIMA (este script se ejecuta el sábado → genera para lunes siguiente)
    hoy = datetime.now()
    dias_desde_lunes = hoy.weekday()
    lunes = hoy - timedelta(days=dias_desde_lunes)
    if hoy.weekday() >= 5:  # Sábado(5) o Domingo(6) → siguiente semana
        lunes = lunes + timedelta(days=7)
    domingo = lunes + timedelta(days=6)

    fecha_inicio   = lunes.strftime("%d/%m/%Y")
    nombre_semana  = f"Lunes {lunes.strftime('%d/%m')} al Domingo {domingo.strftime('%d/%m/%Y')}"
    print(f"📅 Generando menú para: {nombre_semana}")

    # Leer historial y feedbacks desde GitHub
    print("\n📂 Leyendo datos del repositorio...")
    historial, historial_sha   = leer_json_github(DATA_HISTORIAL_PATH)
    feedbacks, feedbacks_sha   = leer_json_github(DATA_FEEDBACKS_PATH)
    historial  = historial  or []
    feedbacks  = feedbacks  or []
    print(f"  📖 Historial: {len(historial)} semanas previas")
    print(f"  💬 Feedbacks: {len(feedbacks)} comentarios de la familia")

    # Construir prompt y llamar a Gemini
    prompt = construir_prompt(fecha_inicio, historial, feedbacks)
    print("\n📡 Consultando Gemini AI...")
    plan = llamar_gemini(prompt)

    # Asegurar campo semana
    plan.setdefault("semana", nombre_semana)
    print(f"  ✅ Menú generado: {plan.get('semana')}")

    # Guardar menú en GitHub
    print("\n💾 Guardando en GitHub...")
     # ── NUEVO: guardar el menú actual como "semana anterior" antes de sobreescribir
    menu_existente, menu_sha = leer_json_github(DATA_MENU_PATH)
    if menu_existente:
        menu_anterior_existente, menu_anterior_sha = leer_json_github("data/menu_anterior.json")
        escribir_json_github(
            "data/menu_anterior.json",
            menu_existente,
            f"historial: guardar semana anterior ({menu_existente.get('semana', '?')})",
            sha=menu_anterior_sha
        )
        print(f"  📦 Semana anterior guardada: {menu_existente.get('semana')}")
    # ── FIN NUEVO
    escribir_json_github(
        DATA_MENU_PATH, plan,
        f"menu: {nombre_semana}",
        sha=menu_sha
    )

    # Actualizar historial
    platos_usados = []
    for dia in plan.get("dias", {}).values():
        for comida in dia.values():
            if isinstance(comida, dict) and "nombre" in comida:
                platos_usados.append(comida["nombre"])

    historial.append({
        "semana": nombre_semana,
        "fecha_generacion": hoy.isoformat(),
        "platos_usados": platos_usados,
    })
    if len(historial) > 6:
        historial = historial[-6:]

    escribir_json_github(
        DATA_HISTORIAL_PATH, historial,
        f"historial: añadida semana {nombre_semana}",
        sha=historial_sha
    )

    # Limpiar feedbacks (ya incorporados al nuevo menú)
    if feedbacks:
        escribir_json_github(
            DATA_FEEDBACKS_PATH, [],
            "feedbacks: limpiar tras generación de menú",
            sha=feedbacks_sha
        )
        print(f"  🗑️  {len(feedbacks)} feedbacks archivados y limpiados")

    print(f"\n{'='*60}")
    print(f"✅ ¡MENÚ GENERADO Y PUBLICADO EXITOSAMENTE!")
    print(f"   Semana: {nombre_semana}")
    print(f"   El sitio web ya muestra el nuevo menú.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
