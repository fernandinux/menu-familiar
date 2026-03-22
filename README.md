# 🍽️ Menú Familiar Paca — Sistema Cloud

Sistema 100% gratuito y automático que genera el menú semanal de la Familia Paca cada sábado a las 7am (Lima), con app web para ver el menú y dejar feedback.

**Tecnologías:** GitHub · Netlify · Render.com · Google Gemini AI
**Costo:** $0 (todos los servicios en plan gratuito)

---

## ¿Cómo funciona?

```
Cada sábado 7am Lima
       ↓
GitHub Actions ejecuta scripts/generar_menu_cloud.py
       ↓
Llama a Gemini AI → genera el menú JSON
       ↓
Guarda menu_actual.json en el repositorio GitHub
       ↓
Frontend Netlify muestra el menú automáticamente
       ↓
La familia puede dar feedback → se guarda en feedbacks.json
       ↓
El próximo sábado, Gemini incorpora el feedback al nuevo menú
```

---

## PASO A PASO — DESPLIEGUE INICIAL

Sigue estos pasos en orden. Solo se hacen una vez.

---

### PASO 1 — Crear el repositorio en GitHub

1. Ve a [github.com](https://github.com) e inicia sesión
2. Clic en el botón verde **"New"** (arriba a la izquierda)
3. Nombre del repositorio: `menu-familiar` (o el que prefieras)
4. Visibilidad: **Private** (recomendado, para no exponer tu API key)
5. Clic en **"Create repository"**
6. **Anota el nombre completo**, ej: `fernando-paca/menu-familiar`

---

### PASO 2 — Subir el código al repositorio

En tu Mac, abre la Terminal y ejecuta:

```bash
# 1. Descomprime el ZIP que recibiste y entra a la carpeta
cd ~/Downloads
unzip menu-familiar-cloud.zip
cd menu-familiar-cloud

# 2. Inicializa git y sube al repositorio que creaste
git init
git add .
git commit -m "primer commit: sistema menu familiar"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/menu-familiar.git
# ⚠️ Reemplaza TU-USUARIO con tu usuario de GitHub

git push -u origin main
```

Si te pide usuario y contraseña de GitHub, usa tu usuario y un **Personal Access Token** (no tu contraseña). Si no tienes uno, ve al PASO 3 primero.

---

### PASO 3 — Crear Personal Access Token en GitHub

Este token permite que el sistema escriba los menús en el repositorio.

1. Ve a [github.com/settings/tokens](https://github.com/settings/tokens)
2. Clic en **"Generate new token (classic)"**
3. Nota (nombre): `menu-familiar-paca`
4. Expiración: `No expiration` (para que no caduque)
5. Permisos: marca la casilla **`repo`** (incluye todo lo de abajo automáticamente)
6. Clic en **"Generate token"** (botón verde al final)
7. **⚠️ IMPORTANTE: Copia el token AHORA** — solo se muestra una vez
   - Se ve así: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
8. Guárdalo en un lugar seguro (Notas, etc.)

---

### PASO 4 — Configurar secretos en GitHub Actions

Los secretos son valores privados que GitHub Actions usa al ejecutarse.

1. Ve a tu repositorio en GitHub
2. Clic en **Settings** (pestaña arriba a la derecha)
3. En el menú izquierdo: **Secrets and variables → Actions**
4. Clic en **"New repository secret"**
5. Agrega estos 2 secretos uno por uno:

**Secreto 1:**
- Name: `GEMINI_API_KEY`
- Secret: `AIzaSyAcxRuDGMKAI4ijzMT2q0vJXORzkbQhe-Q`
- Clic en "Add secret"

**Secreto 2:**
- Name: `GITHUB_TOKEN`  
- Secret: el token que copiaste en el PASO 3 (`ghp_xxx...`)
- Clic en "Add secret"

> 💡 **Nota:** El `GITHUB_TOKEN` secreto integrado de Actions no tiene permisos para escribir en el repo desde el script Python. Por eso necesitamos uno personalizado.

---

### PASO 5 — Desplegar el backend en Render.com

El backend recibe los feedbacks de la familia y sirve el menú.

1. Ve a [render.com](https://render.com) y crea una cuenta gratuita (con tu email)
2. En el dashboard, clic en **"New +"** → **"Web Service"**
3. Conecta tu cuenta de GitHub (clic en "Connect account")
4. Busca y selecciona tu repositorio `menu-familiar`
5. Configura el servicio:
   - **Name:** `menu-familiar-paca`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
6. Más abajo, en **"Environment Variables"**, agrega estas variables:

   | Key | Value |
   |-----|-------|
   | `GITHUB_TOKEN` | tu token de GitHub (el mismo del PASO 3) |
   | `GITHUB_REPO` | `tu-usuario/menu-familiar` (nombre completo del repo) |
   | `GITHUB_BRANCH` | `main` |

7. Clic en **"Create Web Service"** (botón morado al final)
8. Espera 2-3 minutos mientras Render instala las dependencias
9. Cuando diga **"Live"**, copia la URL del servicio:
   - Se ve así: `https://menu-familiar-paca.onrender.com`
   - **Anota esta URL** — la necesitas en el siguiente paso

---

### PASO 6 — Conectar el frontend con el backend

El frontend necesita saber la URL del backend para hacer las consultas.

1. En tu Mac, abre el archivo `frontend/index.html`
2. Busca esta línea (cerca del inicio):
   ```html
   <script>window.API_URL = "%%BACKEND_URL%%";</script>
   ```
3. Reemplázala con tu URL real de Render:
   ```html
   <script>window.API_URL = "https://menu-familiar-paca.onrender.com";</script>
   ```
   ⚠️ Sin `/` al final de la URL
4. Guarda el archivo
5. Sube el cambio a GitHub:
   ```bash
   cd ~/Downloads/menu-familiar-cloud
   git add frontend/index.html
   git commit -m "config: URL del backend de Render"
   git push
   ```

---

### PASO 7 — Desplegar el frontend en Netlify

1. Ve a [netlify.com](https://netlify.com) y crea una cuenta gratuita
2. Clic en **"Add new site"** → **"Import an existing project"**
3. Clic en **"GitHub"** y autoriza el acceso
4. Busca y selecciona tu repositorio `menu-familiar`
5. Configuración del build:
   - **Base directory:** (dejar vacío)
   - **Build command:** (dejar vacío)
   - **Publish directory:** `frontend`
6. Clic en **"Deploy site"**
7. En 1-2 minutos tendrás una URL como:
   - `https://nombre-aleatorio.netlify.app`
8. Opcional — cambiar a un nombre personalizado:
   - En Netlify, ve a **Site configuration → Change site name**
   - Escribe: `menu-paca` → URL queda: `https://menu-paca.netlify.app`

---

### PASO 8 — Probar que todo funciona

1. Abre la URL de tu sitio Netlify en el celular
2. Verifica que el menú carga (puede tardar ~30 segundos la primera vez — Render está despertando)
3. Ve a la pestaña **"Feedback"** y envía un feedback de prueba
4. Verifica que aparece en "Feedbacks recientes"

---

### PASO 9 — Primer menú manual (opcional)

El primer menú automático se generará el próximo sábado. Si quieres verlo hoy:

1. Ve a tu repositorio en GitHub
2. Clic en **Actions** (pestaña superior)
3. Clic en **"Generar Menú Semanal"** (en el menú izquierdo)
4. Clic en **"Run workflow"** → **"Run workflow"** (botón verde)
5. Espera ~2 minutos
6. Recarga el sitio — ya tiene el menú nuevo

---

## ESTRUCTURA DEL REPOSITORIO

```
menu-familiar/
├── frontend/                  ← Sitio web (Netlify lo publica)
│   ├── index.html             ← App principal (Menú, Compras, Feedback)
│   └── static/
│       ├── css/style.css      ← Estilos (modo claro/oscuro)
│       └── js/app.js          ← Lógica del frontend
│
├── backend/                   ← API Python (Render.com la ejecuta)
│   ├── main.py                ← FastAPI: /menu-actual, /feedback, /feedbacks
│   └── requirements.txt      ← Dependencias Python
│
├── scripts/
│   └── generar_menu_cloud.py  ← Script que genera el menú con Gemini AI
│
├── data/                      ← Datos (GitHub los almacena)
│   ├── menu_actual.json       ← Menú de la semana actual
│   ├── feedbacks.json         ← Feedback de la familia
│   └── historial.json         ← Historial para evitar repetir platos
│
├── .github/
│   └── workflows/
│       └── generar-menu.yml   ← Automatización: sábados 7am Lima
│
├── netlify.toml               ← Config de Netlify
├── render.yaml                ← Config de Render.com
└── README.md                  ← Este archivo
```

---

## CÓMO COMPARTIR EL MENÚ POR WHATSAPP

La app web es perfecta para WhatsApp:
1. Abre el sitio en tu celular
2. Comparte el enlace por WhatsApp con la familia
   - Roxana (cocinera) y Luna (nana) pueden ver el menú y dar feedback
3. Todos pueden dejar feedback en la pestaña "Feedback"

---

## RECORDATORIOS IMPORTANTES

**Render.com free tier:**
- El servicio "duerme" si no recibe visitas en 15 minutos
- La primera vez que alguien abre el sitio puede tardar ~30 segundos en despertar
- Esto es normal — mientras carga verás el mensaje "El servidor está despertando"

**GitHub Actions:**
- El menú se genera automáticamente cada sábado a las 7:00 AM Lima
- Si hay algún error, recibirás un email de GitHub Actions
- Puedes ver el historial de ejecuciones en tu repo → pestaña Actions

**Si Gemini AI falla:**
- Ve al repo → Actions → "Generar Menú Semanal" → Run workflow
- El script se reintentará automáticamente

---

## CAMBIAR O MEJORAR EL PROMPT

Para modificar las reglas nutricionales, edita el archivo `scripts/generar_menu_cloud.py`, sección `PROMPT_SISTEMA` (alrededor de la línea 35). 

Tras editar, sube el cambio a GitHub y el próximo sábado usará el nuevo prompt.

---

## SOPORTE

Creado con [Perplexity Computer](https://www.perplexity.ai/computer) — Familia Paca, Lima Perú
