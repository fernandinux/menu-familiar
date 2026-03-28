/* ============================================================
   MENÚ FAMILIAR PACA — app.js
   Conecta con el backend FastAPI en Render.com
   ============================================================ */

// ── CONFIG ───────────────────────────────────────────────────
const API = (window.API_URL || '').replace(/\/$/, '');
if (!API || API === '%%BACKEND_URL%%') {
  console.warn('[Paca] API_URL no configurada. Ver README para instrucciones.');
}

// ── DARK MODE TOGGLE ─────────────────────────────────────────
(function () {
  const toggle = document.querySelector('[data-theme-toggle]');
  const root = document.documentElement;
  let theme = matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
  root.setAttribute('data-theme', theme);

  const sun = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`;
  const moon = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;

  const updateIcon = () => { if (toggle) toggle.innerHTML = theme === 'dark' ? sun : moon; };
  updateIcon();

  if (toggle) {
    toggle.addEventListener('click', () => {
      theme = theme === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', theme);
      updateIcon();
    });
  }
})();

// ── TAB NAVIGATION ───────────────────────────────────────────
const tabs = document.querySelectorAll('.nav-tab');
const panels = document.querySelectorAll('.tab-section');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    const id = `tab-${tab.dataset.tab}`;
    document.getElementById(id)?.classList.add('active');
    if (tab.dataset.tab === 'feedback') loadFeedbacks();
    if (tab.dataset.tab === 'anterior') loadMenuAnterior();
  });
});

// ── TOAST ────────────────────────────────────────────────────
const toastEl = document.getElementById('toast');
let toastTimer;
function toast(msg, duration = 3000) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), duration);
}

// ── WAKE-UP BANNER (Render.com cold start) ───────────────────
let wakeTimer;
function showWakeBanner(container) {
  wakeTimer = setTimeout(() => {
    const existing = container.querySelector('.wake-banner');
    if (existing) return;
    const banner = document.createElement('div');
    banner.className = 'wake-banner';
    banner.innerHTML = `<span>⏳</span><span>El servidor está despertando (puede tardar ~30 seg la primera vez)…</span>`;
    container.insertBefore(banner, container.firstChild);
  }, 2000);
}
function clearWakeBanner(container) {
  clearTimeout(wakeTimer);
  container.querySelector('.wake-banner')?.remove();
}

// ── FETCH CON RETRY (para cold start de Render) ──────────────
async function fetchConRetry(url, container, intentosMax = 3) {
  let res;
  for (let intento = 1; intento <= intentosMax; intento++) {
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 55000);
      res = await fetch(url, { signal: ctrl.signal });
      clearTimeout(timer);
      return res;
    } catch (fetchErr) {
      if (intento === intentosMax) throw fetchErr;
      if (container) {
        container.innerHTML = `<div class="loader-box"><div class="spinner"></div><p>Despertando servidor… (intento ${intento}/${intentosMax})</p></div>`;
      }
      await new Promise(r => setTimeout(r, 3000));
    }
  }
}

// ── HELPERS ──────────────────────────────────────────────────
const DIAS_ES = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];
const DIAS_LABEL = {
  lunes: 'Lunes', martes: 'Martes', miercoles: 'Miércoles',
  jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sábado', domingo: 'Domingo'
};

function escHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatFecha(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ── LONCHERA DATA ─────────────────────────────────────────────
// Cache de la lonchera cargada desde el backend
let loncheraData = null;

async function cargarLonchera() {
  if (loncheraData) return loncheraData;
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 55000);
    const res = await fetch(`${API}/lonchera`, { signal: ctrl.signal });
    if (!res.ok) return null;
    loncheraData = await res.json();
    return loncheraData;
  } catch {
    return null;
  }
}

// Genera el HTML del bloque de lonchera para un día dado
function renderLoncheraBloque(dia, lonchera) {
  if (!lonchera) return '';

  // Si es texto libre (nuevo formato)
  if (lonchera.texto_libre) {
    // Buscar el día en el texto libre
    const texto = lonchera.texto_libre;
    const labelDia = DIAS_LABEL[dia] || dia;
    // Extraer el bloque del día del texto libre
    const regex = new RegExp(`${labelDia}[:\\s]*([\\s\\S]*?)(?=(?:Lunes|Martes|Miércoles|Miercoles|Jueves|Viernes|Sábado|Sabado|Domingo):|$)`, 'i');
    const match = texto.match(regex);
    if (!match || !match[1].trim()) return '';
    const contenido = escHtml(match[1].trim()).replace(/\n/g, '<br>');
    return `
      <div class="meal-block lonchera-block">
        <div class="meal-type-badge">🎒 Lonchera</div>
        <div class="lonchera-text">${contenido}</div>
      </div>`;
  }

  // Formato estructurado (JSON con dias)
  const diasData = lonchera.dias || {};
  const diaKey = dia === 'miercoles' ? 'miercoles' : dia;
  const diaLonchera = diasData[diaKey];

  // Solo lunes–viernes tienen lonchera
  if (!diaLonchera || dia === 'sabado' || dia === 'domingo') return '';

  const facundo  = diaLonchera.facundo  || '';
  const leonardo = diaLonchera.leonardo || '';
  if (!facundo && !leonardo) return '';

  let items = '';
  if (facundo)  items += `<div class="lonchera-item"><span class="lonchera-quien">🧩 Facundo:</span> ${escHtml(facundo)}</div>`;
  if (leonardo) items += `<div class="lonchera-item"><span class="lonchera-quien">👦 Leonardo:</span> ${escHtml(leonardo)}</div>`;

  return `
    <div class="meal-block lonchera-block">
      <div class="meal-type-badge">🎒 Lonchera</div>
      ${items}
    </div>`;
}

// ── LOAD MENU ────────────────────────────────────────────────
let menuData = null;

async function loadMenu() {
  const container = document.getElementById('menu-container');
  const semanaLabel = document.getElementById('semana-label');
  const semanaLabelC = document.getElementById('semana-label-compras');

  container.innerHTML = `<div class="loader-box"><div class="spinner"></div><p>Cargando menú…</p></div>`;
  showWakeBanner(container);

  try {
    // Cargar menú y lonchera en paralelo
    const [res, lonchera] = await Promise.all([
      fetchConRetry(`${API}/menu-actual`, container),
      cargarLonchera()
    ]);
    clearWakeBanner(container);

    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    menuData = data;
    loncheraData = lonchera;

    if (semanaLabel) semanaLabel.textContent = data.semana || '';
    if (semanaLabelC) semanaLabelC.textContent = data.semana || '';

    renderMenu(data, container);
    renderCompras(data);

  } catch (err) {
    clearWakeBanner(container);
    container.innerHTML = `
      <div class="loader-box">
        <p>⚠️ No se pudo cargar el menú.</p>
        <p style="font-size:var(--text-xs);color:var(--color-text-faint);margin-top:0.5rem">${escHtml(err.message)}</p>
        <button class="btn-primary" style="width:auto;margin-top:1rem" onclick="loadMenu()">Reintentar</button>
      </div>`;
    console.error('[Paca] loadMenu:', err);
  }
}

// ── RENDER MENU CARDS ─────────────────────────────────────────
function renderMenu(data, container) {
  const dias = data.dias || {};
  let html = '<div class="menu-grid">';

  DIAS_ES.forEach(dia => {
    const d = dias[dia];
    if (!d) return;
    const label = DIAS_LABEL[dia] || dia;
    const diaClass = `day-${dia.replace('é', 'e').replace('á', 'a').replace('ó', 'o')}`;

    html += `
      <div class="day-card ${diaClass}">
        <div class="day-header">
          <div class="day-dot"></div>
          <span class="day-name">${label}</span>
        </div>`;

    // Desayuno
    const desayuno = d['desayuno'];
    if (desayuno) {
      const tags = (desayuno.ingredientes_principales || []).slice(0, 4)
        .map(t => `<span class="meal-tag">${escHtml(t)}</span>`).join('');
      let notes = '';
      if (desayuno.nota_facundo)  notes += `<div class="meal-note facundo">🧩 Facundo: ${escHtml(desayuno.nota_facundo)}</div>`;
      if (desayuno.nota_fernando) notes += `<div class="meal-note fernando">💚 Fernando: ${escHtml(desayuno.nota_fernando)}</div>`;
      html += `
        <div class="meal-block">
          <div class="meal-type-badge">☀️ Desayuno</div>
          <div class="meal-name">${escHtml(desayuno.nombre || '—')}</div>
          ${desayuno.descripcion ? `<p class="meal-desc">${escHtml(desayuno.descripcion)}</p>` : ''}
          ${tags ? `<div class="meal-tags">${tags}</div>` : ''}
          ${notes ? `<div class="meal-notes">${notes}</div>` : ''}
        </div>`;
    }

    // Lonchera (solo lunes–viernes, entre desayuno y almuerzo)
    if (dia !== 'sabado' && dia !== 'domingo') {
      html += renderLoncheraBloque(dia, loncheraData);
    }

    // Almuerzo
    const almuerzo = d['almuerzo'];
    if (almuerzo) {
      const tags = (almuerzo.ingredientes_principales || []).slice(0, 4)
        .map(t => `<span class="meal-tag">${escHtml(t)}</span>`).join('');
      let notes = '';
      if (almuerzo.nota_facundo)  notes += `<div class="meal-note facundo">🧩 Facundo: ${escHtml(almuerzo.nota_facundo)}</div>`;
      if (almuerzo.nota_fernando) notes += `<div class="meal-note fernando">💚 Fernando: ${escHtml(almuerzo.nota_fernando)}</div>`;
      if (almuerzo.nota_domingo)  notes += `<div class="meal-note" style="border-color:var(--day-domingo)">📌 ${escHtml(almuerzo.nota_domingo)}</div>`;
      html += `
        <div class="meal-block">
          <div class="meal-type-badge">🍽️ Almuerzo</div>
          <div class="meal-name">${escHtml(almuerzo.nombre || '—')}</div>
          ${almuerzo.descripcion ? `<p class="meal-desc">${escHtml(almuerzo.descripcion)}</p>` : ''}
          ${tags ? `<div class="meal-tags">${tags}</div>` : ''}
          ${notes ? `<div class="meal-notes">${notes}</div>` : ''}
        </div>`;
    }

    html += `</div>`;
  });

  html += '</div>';
  container.innerHTML = html;
}

// ── RENDER SHOPPING LISTS ─────────────────────────────────────
function renderCompras(data) {
  const container = document.getElementById('compras-container');
  if (!container) return;

  const CATEGORIAS = {
    carnes_y_proteinas: { label: '🥩 Carnes y proteínas' },
    vegetales_y_frutas: { label: '🥦 Vegetales y frutas' },
    lacteos_y_huevos:   { label: '🥚 Lácteos y huevos' },
    despensa:           { label: '🧂 Despensa' },
  };

  function buildCard(lista, titulo, subtitulo, iconClass) {
    if (!lista) return '';
    let body = '';
    Object.entries(CATEGORIAS).forEach(([key, cat]) => {
      const items = lista[key] || [];
      if (!items.length) return;
      body += `<div class="categoria-title">${cat.label}</div>`;
      body += `<ul class="compras-list">${items.map(i => `<li class="compras-item">${escHtml(i)}</li>`).join('')}</ul>`;
    });
    if (!body) return '';
    const desc = lista.descripcion ? `<p style="font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-2)">${escHtml(lista.descripcion)}</p>` : '';
    return `
      <div class="compras-card">
        <div class="compras-header">
          <div class="compras-icon ${iconClass}">${iconClass === 'domingo' ? '🛒' : '🏪'}</div>
          <div>
            <div class="compras-title">${titulo}</div>
            <div class="compras-subtitle">${subtitulo}</div>
            ${desc}
          </div>
        </div>
        <div class="compras-body">${body}</div>
      </div>`;
  }

  const c1 = buildCard(data.lista_compras_domingos, 'Compra del Domingo', 'Para lunes–miércoles', 'domingo');
  const c2 = buildCard(data.lista_compras_mitad_semana, 'Compra a Mitad de Semana', 'Para jueves–domingo', 'mitad');
  container.innerHTML = `<div class="compras-grid">${c1}${c2}</div>`;
}

// ── FEEDBACK FORM ─────────────────────────────────────────────
let selectedQuien = 'Fernando';
let selectedTipos = new Set();

document.querySelectorAll('#chips-quien .chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#chips-quien .chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedQuien = btn.dataset.val;
  });
});

document.querySelectorAll('#chips-tipo .chip').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.classList.toggle('active');
    const val = btn.dataset.val;
    if (selectedTipos.has(val)) selectedTipos.delete(val);
    else selectedTipos.add(val);
    updateConditionalFields();
  });
});

function updateConditionalFields() {
  const platoField = document.getElementById('field-plato');
  const ingField   = document.getElementById('field-ingrediente');
  const cantField  = document.getElementById('field-cantidad');

  if (platoField) platoField.hidden = !selectedTipos.has('no_gusto');
  if (ingField)   ingField.hidden   = !selectedTipos.has('ingrediente');
  if (cantField)  cantField.hidden  = !selectedTipos.has('cantidad');

  if (!platoField?.hidden && menuData) {
    const sel = document.getElementById('sel-plato');
    if (sel && sel.options.length <= 1) {
      const dias = menuData.dias || {};
      DIAS_ES.forEach(dia => {
        const d = dias[dia];
        if (!d) return;
        const label = DIAS_LABEL[dia] || dia;
        ['desayuno', 'almuerzo'].forEach(comida => {
          const m = d[comida];
          if (!m?.nombre) return;
          const opt = new Option(`${label} — ${m.nombre}`, `${dia}|${comida}|${m.nombre}`);
          sel.add(opt);
        });
      });
    }
  }
}

const feedbackForm = document.getElementById('feedback-form');
if (feedbackForm) {
  feedbackForm.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('btn-submit');

    if (selectedTipos.size === 0) {
      toast('Elige al menos un tipo de feedback');
      return;
    }

    const payload = {
      quien:       selectedQuien,
      tipos:       [...selectedTipos],
      plato:       document.getElementById('sel-plato')?.value || null,
      ingrediente: document.getElementById('inp-ingrediente')?.value || null,
      cantidad:    document.getElementById('inp-cantidad')?.value || null,
      comentario:  document.getElementById('inp-comentario')?.value || null,
    };

    btn.disabled = true;
    btn.textContent = 'Enviando…';

    try {
      const res = await fetch(`${API}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000),
      });

      if (!res.ok) throw new Error((await res.text()) || `Error ${res.status}`);

      toast('✅ ¡Feedback enviado! Gracias 🙏');
      feedbackForm.reset();
      selectedTipos.clear();
      document.querySelectorAll('#chips-tipo .chip').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('#chips-quien .chip').forEach(b => b.classList.remove('active'));
      document.querySelector('#chips-quien .chip[data-val="Fernando"]')?.classList.add('active');
      selectedQuien = 'Fernando';
      updateConditionalFields();
      loadFeedbacks();

    } catch (err) {
      toast(`⚠️ Error: ${err.message}`);
      console.error('[Paca] feedback submit:', err);
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Enviar feedback <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }
  });
}

// ── LOAD FEEDBACKS ────────────────────────────────────────────
const TIPO_LABELS = {
  no_gusto:    '😕 No gustó',
  ingrediente: '🛒 Ingrediente difícil',
  cantidad:    '⚖️ Cantidad incorrecta',
  comentario:  '💬 Comentario libre',
};

async function loadFeedbacks() {
  const container = document.getElementById('historial-container');
  if (!container) return;
  container.innerHTML = `<div class="loader-box" style="padding:var(--space-6)"><div class="spinner"></div></div>`;

  try {
    const res = await fetch(`${API}/feedbacks`, { signal: AbortSignal.timeout(30000) });
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const items = await res.json();

    if (!items.length) {
      container.innerHTML = `<p class="empty">Aún no hay feedbacks esta semana.</p>`;
      return;
    }

    const sorted = [...items].reverse();
    container.innerHTML = sorted.map(fb => {
      const tipos = (fb.tipos || []).map(t =>
        `<span class="fb-tipo-badge">${TIPO_LABELS[t] || t}</span>`).join('');
      const extras = [
        fb.plato       ? `Plato: ${escHtml(fb.plato.split('|').pop())}` : null,
        fb.ingrediente ? `Ingrediente: ${escHtml(fb.ingrediente)}` : null,
        fb.cantidad    ? `Cantidad: ${escHtml(fb.cantidad)}` : null,
      ].filter(Boolean).join(' · ');
      const comentario = fb.comentario || extras;

      return `
        <div class="fb-item">
          <div class="fb-meta">
            <span class="fb-quien">${escHtml(fb.quien)}</span>
            <span class="fb-fecha">${formatFecha(fb.fecha)}</span>
          </div>
          <div class="fb-tipos">${tipos}</div>
          ${comentario ? `<p class="fb-comentario">${escHtml(comentario)}</p>` : ''}
        </div>`;
    }).join('');

  } catch (err) {
    container.innerHTML = `<p class="empty">No se pudo cargar el historial.</p>`;
    console.error('[Paca] loadFeedbacks:', err);
  }
}

// ── LONCHERA FORM ─────────────────────────────────────────────
const loncheraForm = document.getElementById('lonchera-form');
if (loncheraForm) {
  loncheraForm.addEventListener('submit', async e => {
    e.preventDefault();
    const btn   = document.getElementById('btn-lonchera');
    const input = document.getElementById('inp-lonchera');
    const texto = input?.value?.trim();

    if (!texto) {
      toast('Escribe la lonchera antes de guardar');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Guardando…';

    try {
      const res = await fetch(`${API}/lonchera`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto }),
        signal: AbortSignal.timeout(30000),
      });

      if (!res.ok) throw new Error((await res.text()) || `Error ${res.status}`);

      toast('✅ Lonchera guardada correctamente');
      // Invalidar caché para que se recargue al ver el menú
      loncheraData = null;
      input.value = '';

    } catch (err) {
      toast(`⚠️ Error al guardar lonchera: ${err.message}`);
      console.error('[Paca] lonchera submit:', err);
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Guardar lonchera <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }
  });
}

// ── LOAD MENÚ ANTERIOR ────────────────────────────────────────
let menuAnteriorCargado = false;

async function loadMenuAnterior() {
  if (menuAnteriorCargado) return;
  const container = document.getElementById('menu-anterior-container');
  const label     = document.getElementById('semana-label-anterior');
  if (!container) return;

  container.innerHTML = `<div class="loader-box"><div class="spinner"></div><p>Cargando semana anterior…</p></div>`;
  showWakeBanner(container);

  try {
    const res = await fetchConRetry(`${API}/menu-anterior`, container);
    clearWakeBanner(container);

    if (res.status === 404) {
      container.innerHTML = `<p class="empty">Aún no hay semana anterior guardada. Estará disponible a partir del próximo sábado.</p>`;
      return;
    }
    if (!res.ok) throw new Error(`Error ${res.status}`);

    const data = await res.json();
    if (label) label.textContent = data.semana || '';
    // El menú anterior NO muestra lonchera (es info histórica)
    renderMenu(data, container);
    menuAnteriorCargado = true;

  } catch (err) {
    clearWakeBanner(container);
    container.innerHTML = `
      <div class="loader-box">
        <p>⚠️ No se pudo cargar el menú anterior.</p>
        <button class="btn-primary" style="width:auto;margin-top:1rem"
          onclick="menuAnteriorCargado=false;loadMenuAnterior()">Reintentar</button>
      </div>`;
    console.error('[Paca] loadMenuAnterior:', err);
  }
}

// ── INIT ──────────────────────────────────────────────────────
loadMenu();
