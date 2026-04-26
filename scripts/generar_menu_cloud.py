"""
GENERADOR DE MENÚ SEMANAL — versión CLOUD v2
Familia Paca, Lima Perú

Cambios v2:
- Memoria acumulativa: los feedbacks se guardan en data/memoria.json y
  se incorporan al prompt de forma permanente (no se borran cada semana)
- Los feedbacks de la semana actual se agregan a la memoria antes de generar
- Viernes: solo desayuno y lonchera, SIN almuerzo (la cocinera decide)
- Desayunos rutinarios y simples, alineados con las meriendas del nido
- La IA recibe las meriendas del mes para no repetir ingredientes en desayunos
- Referencias a páginas web de recetas peruanas para almuerzos
- Cada plato de almuerzo incluye URL de referencia de receta

Variables de entorno requeridas:
  GEMINI_API_KEY   — clave de Google Gemini
  GITHUB_TOKEN     — PAT para escribir en el repo
  GITHUB_REPO      — ej: "fernandinux/menu-familiar"
  GITHUB_BRANCH    — rama (default: main)
"""

import json, os, ssl, sys, base64
from datetime import datetime, timedelta

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
DATA_MENU_ANT_PATH  = "data/menu_anterior.json"
DATA_FEEDBACKS_PATH = "data/feedbacks.json"
DATA_HISTORIAL_PATH = "data/historial.json"
DATA_MEMORIA_PATH   = "data/memoria.json"       # ← NUEVO: memoria permanente
DATA_LONCHERA_PATH  = "data/lonchera.json"

# ── PÁGINAS DE RECETAS PERUANAS ───────────────────────────────
PAGINAS_RECETAS = [
    "https://cookpad.com/pe",
    "https://buenazo.pe",
    "https://www.recetasnestle.com.pe",
    "https://www.yanuq.com/recetasperuanas.asp",
    "https://comidasperuanas.pe",
    "https://perucomidas.com",
    "https://comidasperuanas.net",
    "https://jameaperu.com",
    "https://perudelicias.com",
    "https://www.ceciliatupac.com",
]

# ── PROMPT SISTEMA (MAESTRO) ──────────────────────────────────
PROMPT_SISTEMA = """
Eres un nutricionista y chef especializado en cocina peruana para familias con necesidades dietéticas específicas en Lima, Perú.
Tu tarea es generar el plan semanal de DESAYUNOS y ALMUERZOS de la familia Paca.

═══════════════════════════════════════════
FAMILIA (6 personas en total)
═══════════════════════════════════════════
- Fernando (padre, adulto): RESISTENCIA A LA INSULINA — controlar carbohidratos refinados
- Lourdes (madre, adulta): sin restricciones
- Facundo (hijo, 4 años): TEA nivel 1 — ver reglas especiales abajo
- Leonardo (hijo, 2 años): en desarrollo, máxima variedad de nutrientes
- Roxana (cocinera, adulta): sin restricciones
- Luna (nana, adulta): sin restricciones

═══════════════════════════════════════════
REGLA FUNDAMENTAL
═══════════════════════════════════════════
UN SOLO MENÚ PARA TODOS. No se preparan platos separados.
El menú debe ser apto simultáneamente para adultos y niños de 2 y 4 años.

═══════════════════════════════════════════
REGLAS PARA FACUNDO (TEA nivel 1)
═══════════════════════════════════════════
PROHIBIDO SIEMPRE:
- Colorantes artificiales, conservantes artificiales
- Glutamato monosódico (MSG/ajinomoto) — si una receta lo incluye, RETIRARLO y anotarlo en nota_facundo
- Alimentos ultraprocesados, grasas trans
- Azúcar refinada en exceso

FAVORECER:
- Omega-3: bonito, jurel, caballa, atún en agua, huevo de corral
- Fibra prebiótica: avena, lentejas, arvejas, zanahoria, plátano
- Probióticos naturales: yogur natural sin azúcar, queso fresco
- Vitaminas B6, B12, C, D y zinc

═══════════════════════════════════════════
REGLAS PARA FERNANDO (Resistencia a la insulina)
═══════════════════════════════════════════
- Porciones MODERADAS de arroz, papa, camote (máx. 2 tazas de arroz para los 6)
- Priorizar: proteínas magras, palta, aceite de oliva, nueces, pecanas
- Desayunos preferentemente sin pan o con pan integral en cantidad mínima
- Ejemplo correcto: "palta entera con pedazos pequeños de pan integral" (no pan con palta)

═══════════════════════════════════════════
REGLAS DE DESAYUNOS (MUY IMPORTANTE)
═══════════════════════════════════════════
1. RUTINARIOS Y SIMPLES: Solo técnicas que entiende una cocinera peruana sin explicación.
   CORRECTO: huevo duro, huevo frito, huevo revuelto, tortilla de huevo, avena cocida, queso fresco
   INCORRECTO: huevos pochados, benedictinos, en cocotte, muffins salados, shakshuka

2. INGREDIENTES SOLO DE LIMA: Todo conseguible en mercados locales.
   NO usar: mantequilla de maní, granola importada, açaí, chía importada, avena instantánea importada

3. LÁCTEOS LIMITADOS PARA FACUNDO (TEA): Máximo 2 veces por semana con lácteos
   (yogur natural o queso fresco). No repetir lácteo dos días seguidos.

4. FRUTAS CON VARIEDAD OBLIGATORIA: No repetir la misma fruta más de 1 vez en la semana.
   Rotar entre: plátano, manzana, papaya, mandarina, mango, pera, maracuyá, aguaymanto,
   granadilla, fresa, naranja. El plátano no debe aparecer más de 1 vez en desayunos de la semana.

5. ALINEADOS CON MERIENDAS DEL NIDO: Si la merienda del día tiene quinua → no poner quinua
   en desayuno. Si tiene huevo → puede estar en desayuno solo si es distinta preparación.
   Si la merienda tiene plátano → no poner plátano en el desayuno de ese día.

6. NO REPETIR INGREDIENTE PRINCIPAL entre desayuno y merienda del mismo día.

7. ESTRUCTURA FIJA DEL DESAYUNO: proteína + fruta (variada) + opcional carbohidrato integral mínimo

8. EJEMPLOS DE DESAYUNOS VÁLIDOS (rotar, no repetir en la semana):
   - Huevo frito con papaya y pan integral tostado (mínimo)
   - Avena cocida con manzana rallada y canela (sin lácteo)
   - Tortilla de huevo con tomate y zanahoria + mandarina
   - Huevo duro con palta y pepino + aguaymanto
   - Yogur natural (sin azúcar) con granola casera de avena + fresa (máx 1 vez/semana)
   - Huevo revuelto con espinaca + mango en trozos
   - Queso fresco con pera + avena cocida (máx 1 vez/semana con queso)

═══════════════════════════════════════════
REGLAS DE ALMUERZOS
═══════════════════════════════════════════
1. RECETAS DE WEBS PERUANAS: Para cada almuerzo, busca una receta real en estas páginas web
   y usa esa URL como referencia:
   - https://cookpad.com/pe
   - https://buenazo.pe
   - https://www.recetasnestle.com.pe
   - https://www.yanuq.com/recetasperuanas.asp
   - https://comidasperuanas.pe
   - https://perucomidas.com
   - https://comidasperuanas.net
   - https://jameaperu.com
   - https://perudelicias.com
   - https://www.ceciliatupac.com

2. ADAPTACIÓN SALUDABLE DE RECETAS: Revisa los ingredientes de cada receta y:
   - Si tiene ajinomoto/MSG → retirarlo, anotar en nota_facundo
   - Si tiene mucha papa → reducir cantidad, agregar más proteína o vegetal
   - Si tiene manteca → reemplazar por aceite de oliva
   - Si es plato fuerte con arroz → reducir porción de arroz o servir sin arroz
   - Ejemplo: chanfainita → poca papa, más bofe; patita con maní → sin arroz

3. PESCADO: Exactamente 1 vez por semana (ni más ni menos). Rotar entre bonito, jurel, pejerrey, caballa.
   El pescado NO puede ir en dos semanas consecutivas si el historial lo muestra.

4. VARIEDAD DE COLORES: mínimo 3 colores de vegetales por almuerzo.

5. LEGUMBRES: al menos 1 vez por semana.

6. VEGETALES NO CRIOLLOS: al menos 2 veces por semana (brócoli, zucchini, berenjena, coliflor, pimientos de colores).

7. VIERNES — ALMUERZO LIBRE: El viernes NO se incluye almuerzo en el menú.
   La cocinera decide el viernes qué cocinar para aprovechar los vegetales
   y carnes que quedan en el refrigerador. Solo incluir desayuno del viernes.

8. DOMINGO: Almuerzo sencillo o que resista bien el recalentamiento (solo 4 personas).

═══════════════════════════════════════════
CANTIDADES
═══════════════════════════════════════════
- Carnes/pescados: 200-250g por adulto, 100-120g por niño → ~1kg a 1.2kg para 6 personas
- Huevos: indicar cantidad exacta de unidades
- Arroz: máximo 2 tazas para los 6
- Domingo almuerzo: solo 4 personas (Fernando, Lourdes, Facundo, Leonardo)

═══════════════════════════════════════════
INGREDIENTES DISPONIBLES EN LIMA, PERÚ
═══════════════════════════════════════════
Proteínas: pollo, res, cerdo, bonito, jurel, caballa, pejerrey, lenguado, corvina, atún en conserva, sardinas, choros, huevos, lentejas, frijoles canarios, pallares, arvejas, garbanzos, hígado de res, bofe, patitas de cerdo
Vegetales: tomate, cebolla, ajo, zanahoria, papa, camote, yuca, choclo, vainita, betarraga, pepino, poro, brócoli, coliflor, espinaca, acelga, zucchini, berenjena, pimiento (rojo/verde/amarillo), apio, lechuga, albahaca, perejil, culantro
Frutas: plátano, papaya, mango, mandarina, naranja, limón, palta, fresa, maracuyá, granadilla, chirimoya, manzana, pera, aguaymanto
Lácteos: leche evaporada, leche fresca, yogur natural, queso fresco, queso edam
Granos: arroz, fideos, pan de molde integral, avena, quinua, kiwicha
Especias: orégano, comino, ají amarillo, ají panca, culantro, perejil, canela, cúrcuma

═══════════════════════════════════════════
FORMATO DE SALIDA — JSON EXACTO
═══════════════════════════════════════════
Devuelve ÚNICAMENTE el JSON sin texto adicional. Para el viernes, incluye solo "desayuno"
en el objeto del día (sin clave "almuerzo"):

{
  "semana": "Lunes DD/MM al Domingo DD/MM/AAAA",
  "dias": {
    "lunes": {
      "desayuno": {
        "nombre": "Nombre del desayuno",
        "descripcion": "Preparación en 1 línea simple y directa",
        "ingredientes_principales": ["ingrediente - cantidad para 6"],
        "nota_facundo": "beneficio o advertencia para Facundo",
        "nota_fernando": "adaptación para resistencia a insulina"
      },
      "almuerzo": {
        "nombre": "Nombre del plato peruano",
        "descripcion": "Preparación en 1 línea, menciona la adaptación saludable si aplica",
        "ingredientes_principales": ["ingrediente - cantidad para 6"],
        "nota_facundo": "si había ajinomoto u otro ingrediente retirado, indicarlo aquí",
        "nota_fernando": "adaptación RI",
        "url_receta": "URL real de la página de recetas donde se basó este plato"
      }
    },
    "martes": { "desayuno": {}, "almuerzo": {} },
    "miercoles": { "desayuno": {}, "almuerzo": {} },
    "jueves": { "desayuno": {}, "almuerzo": {} },
    "viernes": {
      "desayuno": {
        "nombre": "",
        "descripcion": "",
        "ingredientes_principales": [],
        "nota_facundo": "",
        "nota_fernando": "",
        "nota_viernes": "El almuerzo del viernes lo decide la cocinera según lo que queda en el refrigerador."
      }
    },
    "sabado": { "desayuno": {}, "almuerzo": {} },
    "domingo": {
      "desayuno": {},
      "almuerzo": {
        "nombre": "",
        "descripcion": "",
        "ingredientes_principales": [],
        "nota_facundo": "",
        "nota_fernando": "",
        "nota_domingo": "por qué es sencillo o resiste recalentamiento",
        "url_receta": "URL de la receta de referencia"
      }
    }
  },
  "lista_compras_domingos": {
    "descripcion": "Compra dominical para lunes, martes, miércoles, jueves",
    "carnes_y_proteinas": ["item - cantidad"],
    "vegetales_y_frutas": ["item - cantidad"],
    "lacteos_y_huevos": ["item - cantidad"],
    "despensa": ["item - cantidad"]
  },
  "lista_compras_mitad_semana": {
    "descripcion": "Compra de mitad de semana para sábado, domingo (viernes libre)",
    "carnes_y_proteinas": ["item - cantidad"],
    "vegetales_y_frutas": ["item - cantidad"],
    "lacteos_y_huevos": ["item - cantidad"],
    "despensa": ["item - cantidad"]
  }
}
"""


def construir_prompt(fecha_inicio: str, historial: list, feedbacks_semana: list,
                     memoria: dict, lonchera: dict) -> str:
    """Construye el prompt completo con historial, memoria permanente, feedbacks y lonchera."""

    # ── Historial: platos usados últimas 4 semanas ──────────
    historial_texto = ""
    if historial:
        platos_previos = []
        for semana in historial[-4:]:
            platos_previos.extend(semana.get("platos_usados", []))
        if platos_previos:
            historial_texto = f"""
## PLATOS USADOS EN LAS ÚLTIMAS 4 SEMANAS (NO REPETIR)
{chr(10).join(f'- {p}' for p in platos_previos)}
"""

    # ── Memoria permanente acumulada ─────────────────────────
    memoria_texto = ""
    reglas_permanentes = memoria.get("reglas_permanentes", [])
    if reglas_permanentes:
        memoria_texto = f"""
## PREFERENCIAS Y REGLAS PERMANENTES DE LA FAMILIA (RESPETAR SIEMPRE)
Estas reglas vienen del feedback acumulado de semanas anteriores y son PERMANENTES:
{chr(10).join(f'- {r}' for r in reglas_permanentes)}
"""

    # ── Feedbacks de esta semana ─────────────────────────────
    feedbacks_texto = ""
    if feedbacks_semana:
        fb_lines = []
        for fb in feedbacks_semana[-30:]:
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
                line += f": ingrediente = {ingrediente}"
            if cantidad:
                line += f": cantidad = {cantidad}"
            if comentario:
                line += f": {comentario}"
            fb_lines.append(line)

        if fb_lines:
            feedbacks_texto = f"""
## FEEDBACK DE ESTA SEMANA (INCORPORAR EN EL MENÚ Y EN LAS REGLAS PERMANENTES)
{chr(10).join(fb_lines)}
"""

    # ── Lonchera/meriendas del nido ──────────────────────────
    lonchera_texto = ""
    if lonchera:
        texto_lon = lonchera.get("texto_libre", "")
        if texto_lon:
            lonchera_texto = f"""
## MERIENDAS FIJAS DEL NIDO ESTE MES (ALINEAR DESAYUNOS)
Los niños llevan estas meriendas al nido de lunes a viernes. El desayuno NO debe
repetir el ingrediente principal de la merienda del mismo día.
{texto_lon}
"""

    prompt = f"""
Genera el plan completo de DESAYUNOS y ALMUERZOS para la semana que comienza el {fecha_inicio}.

RECUERDA:
- Viernes: solo desayuno (sin almuerzo — la cocinera decide según lo que queda)
- Cada almuerzo debe tener una URL real de alguna de las páginas de recetas peruanas indicadas
- Los desayunos deben usar técnicas simples que entienda una cocinera peruana (huevo duro, frito, revuelto, tortilla, avena cocida)
- NO repetir ingrediente principal del desayuno con la merienda del mismo día
- Pescado: máximo 1 vez esta semana
- Devuelve ÚNICAMENTE el JSON, sin texto adicional
{historial_texto}
{memoria_texto}
{feedbacks_texto}
{lonchera_texto}
"""
    return prompt


def construir_prompt_memoria(feedbacks: list, memoria_actual: dict) -> str:
    """Prompt para que Gemini extraiga reglas permanentes de los feedbacks."""
    fb_text = "\n".join([
        f"- {fb.get('quien','?')} [{', '.join(fb.get('tipos',[]))}]: "
        f"{fb.get('comentario','')} plato={fb.get('plato','')} "
        f"ingrediente={fb.get('ingrediente','')} cantidad={fb.get('cantidad','')}"
        for fb in feedbacks
    ])

    reglas_existentes = "\n".join(
        f"- {r}" for r in memoria_actual.get("reglas_permanentes", [])
    )

    return f"""
Eres el asistente de memoria del sistema de menú familiar Paca.

Tu tarea: analizar los feedbacks de esta semana y extraer reglas permanentes que
deben recordarse para SIEMPRE en la generación de menús futuros.

FEEDBACKS DE ESTA SEMANA:
{fb_text}

REGLAS PERMANENTES YA EXISTENTES (no duplicar):
{reglas_existentes if reglas_existentes else "(ninguna aún)"}

Instrucciones:
1. Analiza cada feedback y extrae una regla clara y accionable
2. No dupliques reglas que ya existen
3. Combina feedbacks similares en una sola regla
4. Sé específico: en lugar de "mejorar cantidades", escribe "aumentar porción de carne para Leonardo a 130g"
5. Devuelve ÚNICAMENTE un JSON con este formato exacto:

{{
  "reglas_nuevas": [
    "regla 1 clara y accionable",
    "regla 2",
    ...
  ],
  "resumen": "resumen en 1 línea de los feedbacks de esta semana"
}}

Si no hay reglas nuevas que agregar, devuelve: {{"reglas_nuevas": [], "resumen": "Sin cambios relevantes"}}
"""


def llamar_gemini(prompt_usuario: str, prompt_sistema: str = None) -> dict:
    """Llama a la API de Gemini 2.5 Flash."""
    import urllib.request, urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    contents = [{"parts": [{"text": prompt_usuario}]}]
    payload = {"contents": contents, "generationConfig": {"temperature": 0.7, "maxOutputTokens": 65536, "responseMimeType": "application/json"}}

    if prompt_sistema:
        payload["system_instruction"] = {"parts": [{"text": prompt_sistema}]}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl_context) as response:
            result = json.loads(response.read().decode("utf-8"))
            finish_reason = result.get("candidates", [{}])[0].get("finishReason", "")
            if finish_reason == "MAX_TOKENS":
                raise Exception("Respuesta cortada por límite de tokens.")
            texto = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if texto.startswith("```json"):
                texto = texto[7:]
            elif texto.startswith("```"):
                texto = texto.split("\n", 1)[1]
            if texto.endswith("```"):
                texto = texto.rsplit("```", 1)[0]
            return json.loads(texto.strip())
    except urllib.error.HTTPError as e:
        raise Exception(f"Error API Gemini ({e.code}): {e.read().decode()}")


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
    _gh_put(content_str=content_str, path=path, message=message, sha=sha)
    print(f"  ✅ {path} actualizado en GitHub")


# ── MAIN ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🍽️  GENERADOR DE MENÚ v2 — FAMILIA PACA (CLOUD)")
    print("=" * 60)

    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY no configurada"); sys.exit(1)
    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN no configurado"); sys.exit(1)
    if not GITHUB_REPO:
        print("❌ ERROR: GITHUB_REPO no configurado"); sys.exit(1)

    # Calcular semana PRÓXIMA
    hoy = datetime.now()
    dias_desde_lunes = hoy.weekday()
    lunes = hoy - timedelta(days=dias_desde_lunes)
    if hoy.weekday() >= 5:
        lunes = lunes + timedelta(days=7)
    domingo = lunes + timedelta(days=6)
    fecha_inicio  = lunes.strftime("%d/%m/%Y")
    nombre_semana = f"Lunes {lunes.strftime('%d/%m')} al Domingo {domingo.strftime('%d/%m/%Y')}"
    print(f"📅 Generando menú para: {nombre_semana}")

    # Leer datos desde GitHub
    print("\n📂 Leyendo datos del repositorio...")
    historial, historial_sha     = leer_json_github(DATA_HISTORIAL_PATH)
    feedbacks, feedbacks_sha     = leer_json_github(DATA_FEEDBACKS_PATH)
    memoria, memoria_sha         = leer_json_github(DATA_MEMORIA_PATH)
    lonchera, _                  = leer_json_github(DATA_LONCHERA_PATH)
    menu_actual, menu_actual_sha = leer_json_github(DATA_MENU_PATH)

    historial = historial or []
    feedbacks = feedbacks or []
    lonchera  = lonchera  or {}

    if memoria is None:
        memoria = {"reglas_permanentes": [], "historial_feedbacks": []}
        memoria_sha = None

    print(f"  📖 Historial: {len(historial)} semanas")
    print(f"  💬 Feedbacks semana: {len(feedbacks)}")
    print(f"  🧠 Reglas permanentes en memoria: {len(memoria.get('reglas_permanentes', []))}")

    # ── PASO 1: Actualizar memoria con feedbacks de esta semana ──
    if feedbacks:
        print("\n🧠 Actualizando memoria permanente con feedbacks...")
        try:
            prompt_mem = construir_prompt_memoria(feedbacks, memoria)
            resultado_mem = llamar_gemini(prompt_mem)
            reglas_nuevas = resultado_mem.get("reglas_nuevas", [])
            resumen       = resultado_mem.get("resumen", "")

            if reglas_nuevas:
                memoria["reglas_permanentes"].extend(reglas_nuevas)
                # Mantener máximo 40 reglas (las más recientes)
                if len(memoria["reglas_permanentes"]) > 40:
                    memoria["reglas_permanentes"] = memoria["reglas_permanentes"][-40:]
                print(f"  ✅ {len(reglas_nuevas)} reglas nuevas agregadas a memoria")
                for r in reglas_nuevas:
                    print(f"     → {r}")

            # Guardar resumen en historial de feedbacks de la memoria
            memoria.setdefault("historial_feedbacks", []).append({
                "semana": nombre_semana,
                "resumen": resumen,
                "feedbacks_count": len(feedbacks),
                "reglas_agregadas": reglas_nuevas
            })
            # Mantener historial de los últimos 12 resúmenes
            memoria["historial_feedbacks"] = memoria["historial_feedbacks"][-12:]

        except Exception as e:
            print(f"  ⚠️  Error actualizando memoria: {e} — continuando sin actualizar")
    else:
        print("\n💬 Sin feedbacks nuevos esta semana")

    # ── PASO 2: Generar menú ─────────────────────────────────
    prompt = construir_prompt(fecha_inicio, historial, feedbacks, memoria, lonchera)
    print("\n📡 Consultando Gemini AI para el menú...")
    plan = llamar_gemini(prompt, PROMPT_SISTEMA)
    plan.setdefault("semana", nombre_semana)
    print(f"  ✅ Menú generado: {plan.get('semana')}")

    # Verificar que el viernes no tiene almuerzo
    viernes = plan.get("dias", {}).get("viernes", {})
    if "almuerzo" in viernes:
        del viernes["almuerzo"]
        print("  🔧 Almuerzo del viernes removido (día libre de cocinera)")

    # ── PASO 3: Guardar todo en GitHub ───────────────────────
    print("\n💾 Guardando en GitHub...")

    # Guardar menú anterior (backup del actual antes de sobreescribir)
    if menu_actual:
        menu_ant, menu_ant_sha = leer_json_github(DATA_MENU_ANT_PATH)
        escribir_json_github(DATA_MENU_ANT_PATH, menu_actual,
                             f"historial: semana anterior ({menu_actual.get('semana','?')})",
                             sha=menu_ant_sha)

    # Guardar nuevo menú
    escribir_json_github(DATA_MENU_PATH, plan,
                         f"menu: {nombre_semana}", sha=menu_actual_sha)

    # Guardar memoria actualizada
    escribir_json_github(DATA_MEMORIA_PATH, memoria,
                         f"memoria: actualizada con feedbacks semana {nombre_semana}",
                         sha=memoria_sha)

    # Actualizar historial
    platos_usados = []
    for dia in plan.get("dias", {}).values():
        for comida_key, comida in dia.items():
            if isinstance(comida, dict) and "nombre" in comida:
                platos_usados.append(comida["nombre"])

    historial.append({
        "semana": nombre_semana,
        "fecha_generacion": hoy.isoformat(),
        "platos_usados": platos_usados,
    })
    if len(historial) > 8:
        historial = historial[-8:]
    escribir_json_github(DATA_HISTORIAL_PATH, historial,
                         f"historial: semana {nombre_semana}", sha=historial_sha)

    # Limpiar feedbacks de la semana (ya incorporados a la memoria)
    if feedbacks:
        escribir_json_github(DATA_FEEDBACKS_PATH, [],
                             "feedbacks: limpiados tras actualizar memoria",
                             sha=feedbacks_sha)
        print(f"  🗑️  {len(feedbacks)} feedbacks incorporados a memoria y limpiados")

    print(f"\n{'='*60}")
    print(f"✅ ¡MENÚ GENERADO Y PUBLICADO EXITOSAMENTE!")
    print(f"   Semana: {nombre_semana}")
    print(f"   Reglas en memoria: {len(memoria.get('reglas_permanentes', []))}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
