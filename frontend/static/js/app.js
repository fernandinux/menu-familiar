/* ============================================================
   MENÚ FAMILIAR PACA — app.js v2
   ============================================================ */

const API = (window.API_URL || '').replace(/\/$/, '');
if (!API || API === '%%BACKEND_URL%%') {
  console.warn('[Paca] API_URL no configurada.');
}

// ── DARK MODE ────────────────────────────────────────────────
(function () {
  const toggle = document.querySelector('[data-theme-toggle]');
  const root   = document.documentElement;
  let theme    = matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
  root.setAttribute('data-theme', theme);
  const sun  = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`;
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

// ── TABS ─────────────────────────────────────────────────────
const tabs   = document.querySelectorAll('.nav-tab');
const panels = document.querySelectorAll('.tab-section');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`tab-${tab.dataset.tab}`)?.classList.add('active');
    if (tab.dataset.tab === 'feedback') loadFeedbacks();
    if (tab.dataset.tab === 'anterior') loadMenuAnterior();
    if (tab.dataset.tab === 'memoria')  loadMemoria();
  });
});


// ── HAMBURGUESA (móvil) ───────────────────────────────────────
const hamburgerBtn  = document.getElementById('hamburger-btn');
const hamburgerMenu = document.getElementById('hamburger-menu');

if (hamburgerBtn && hamburgerMenu) {
  hamburgerBtn.addEventListener('click', () => {
    const isOpen = !hamburgerMenu.hidden;
    hamburgerMenu.hidden = isOpen;
    hamburgerBtn.classList.toggle('open', !isOpen);
    hamburgerBtn.setAttribute('aria-expanded', String(!isOpen));
  });

  // Ítems del menú hamburguesa activan el tab correspondiente
  hamburgerMenu.querySelectorAll('.hamburger-item').forEach(item => {
    item.addEventListener('click', () => {
      const tabTarget = item.dataset.tab;
      // Activar el tab en ambas navs
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      // Marcar el hamburger-item como activo
      hamburgerMenu.querySelectorAll('.hamburger-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      // Mostrar panel
      document.getElementById(`tab-${tabTarget}`)?.classList.add('active');
      // Cerrar menú
      hamburgerMenu.hidden = true;
      hamburgerBtn.classList.remove('open');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
      // Cargar datos del tab
      if (tabTarget === 'feedback') loadFeedbacks();
      if (tabTarget === 'anterior') loadMenuAnterior();
      if (tabTarget === 'memoria')  loadMemoria();
    });
  });

  // Cerrar al hacer clic fuera
  document.addEventListener('click', (e) => {
    if (!hamburgerBtn.contains(e.target) && !hamburgerMenu.contains(e.target)) {
      hamburgerMenu.hidden = true;
      hamburgerBtn.classList.remove('open');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

// ── TOAST ────────────────────────────────────────────────────
const toastEl = document.getElementById('toast');
let toastTimer;
function toast(msg, duration = 3500) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), duration);
}

// ── WAKE BANNER ───────────────────────────────────────────────
let wakeTimer;
function showWakeBanner(container) {
  wakeTimer = setTimeout(() => {
    if (container.querySelector('.wake-banner')) return;
    const b = document.createElement('div');
    b.className = 'wake-banner';
    b.innerHTML = `<span>⏳</span><span>El servidor está despertando (~30 seg la primera vez)…</span>`;
    container.insertBefore(b, container.firstChild);
  }, 2000);
}
function clearWakeBanner(container) {
  clearTimeout(wakeTimer);
  container.querySelector('.wake-banner')?.remove();
}

// ── FETCH CON RETRY ───────────────────────────────────────────
async function fetchConRetry(url, container, max = 3) {
  for (let i = 1; i <= max; i++) {
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 55000);
      const res   = await fetch(url, { signal: ctrl.signal });
      clearTimeout(timer);
      return res;
    } catch (err) {
      if (i === max) throw err;
      if (container) container.innerHTML = `<div class="loader-box"><div class="spinner"></div><p>Despertando servidor… (intento ${i}/${max})</p></div>`;
      await new Promise(r => setTimeout(r, 3000));
    }
  }
}

// ── HELPERS ──────────────────────────────────────────────────
const DIAS_ES = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'];
const DIAS_LABEL = {
  lunes:'Lunes', martes:'Martes', miercoles:'Miércoles',
  jueves:'Jueves', viernes:'Viernes', sabado:'Sábado', domingo:'Domingo'
};

function escHtml(str) {
  return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function formatFecha(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('es-PE',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
}

// ── LONCHERA CACHE ────────────────────────────────────────────
let loncheraData = null;

async function cargarLonchera() {
  if (loncheraData) return loncheraData;
  try {
    const res = await fetch(`${API}/lonchera`, { signal: AbortSignal.timeout(30000) });
    if (!res.ok) return null;
    loncheraData = await res.json();
    return loncheraData;
  } catch { return null; }
}

function renderLoncheraBloque(dia, lonchera) {
  if (!lonchera || dia === 'sabado' || dia === 'domingo') return '';

  if (lonchera.texto_libre) {
    const labelDia = DIAS_LABEL[dia] || dia;
    const regex = new RegExp(
      `${labelDia}[:\\s*]*([\\s\\S]*?)(?=(?:Lunes|Martes|Mi[eé]rcoles|Jueves|Viernes|S[aá]bado|Domingo)[:\\s*]|$)`, 'i'
    );
    const match = lonchera.texto_libre.match(regex);
    if (!match || !match[1].trim()) return '';
    const contenido = escHtml(match[1].trim()).replace(/\n/g, '<br>');
    return `<div class="meal-block lonchera-block">
      <div class="meal-type-badge">🎒 Merienda Nido</div>
      <div class="lonchera-text">${contenido}</div>
    </div>`;
  }

  const d = (lonchera.dias || {})[dia];
  if (!d) return '';
  let items = '';
  if (d.facundo)  items += `<div class="lonchera-item"><span class="lonchera-quien">🧩 Facundo:</span> ${escHtml(d.facundo)}</div>`;
  if (d.leonardo) items += `<div class="lonchera-item"><span class="lonchera-quien">👦 Leonardo:</span> ${escHtml(d.leonardo)}</div>`;
  if (!items) return '';
  return `<div class="meal-block lonchera-block">
    <div class="meal-type-badge">🎒 Merienda Nido</div>
    ${items}
  </div>`;
}

// ── RENDER MEAL BLOCK ─────────────────────────────────────────
function renderMealBlock(m, tipo, dia) {
  if (!m) return '';
  const emoji = tipo === 'desayuno' ? '☀️' : '🍽️';
  const tags  = (m.ingredientes_principales || []).slice(0,4)
    .map(t => `<span class="meal-tag">${escHtml(t)}</span>`).join('');

  let notes = '';
  if (m.nota_facundo)  notes += `<div class="meal-note facundo">🧩 Facundo: ${escHtml(m.nota_facundo)}</div>`;
  if (m.nota_fernando) notes += `<div class="meal-note fernando">💚 Fernando: ${escHtml(m.nota_fernando)}</div>`;
  if (m.nota_domingo)  notes += `<div class="meal-note" style="border-color:var(--day-domingo)">📌 ${escHtml(m.nota_domingo)}</div>`;
  if (m.nota_viernes)  notes += `<div class="meal-note" style="border-color:var(--day-viernes)">🍳 ${escHtml(m.nota_viernes)}</div>`;

  // Link de receta (solo en almuerzos)
  let recetaLink = '';
  if (tipo === 'almuerzo' && m.url_receta) {
    const dominio = (() => { try { return new URL(m.url_receta).hostname.replace('www.',''); } catch { return m.url_receta; } })();
    recetaLink = `<a class="receta-link" href="${escHtml(m.url_receta)}" target="_blank" rel="noopener">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
      Ver receta en ${escHtml(dominio)}
    </a>`;
  }

  return `<div class="meal-block">
    <div class="meal-type-badge">${emoji} ${tipo.charAt(0).toUpperCase()+tipo.slice(1)}</div>
    <div class="meal-name">${escHtml(m.nombre||'—')}</div>
    ${m.descripcion ? `<p class="meal-desc">${escHtml(m.descripcion)}</p>` : ''}
    ${recetaLink}
    ${tags ? `<div class="meal-tags">${tags}</div>` : ''}
    ${notes ? `<div class="meal-notes">${notes}</div>` : ''}
  </div>`;
}

// ── RENDER MENU ───────────────────────────────────────────────
function renderMenu(data, container, mostrarLonchera = true) {
  const dias = data.dias || {};
  let html = '<div class="menu-grid">';

  DIAS_ES.forEach(dia => {
    const d = dias[dia];
    if (!d) return;
    const label    = DIAS_LABEL[dia] || dia;
    const diaClass = `day-${dia.replace('é','e').replace('á','a').replace('ó','o')}`;
    const esViernes = dia === 'viernes';

    html += `<div class="day-card ${diaClass}">
      <div class="day-header">
        <div class="day-dot"></div>
        <span class="day-name">${label}</span>
        ${esViernes ? '<span class="viernes-badge">Almuerzo libre 🍳</span>' : ''}
      </div>`;

    // Desayuno
    html += renderMealBlock(d.desayuno, 'desayuno', dia);

    // Merienda nido (lunes–viernes, entre desayuno y almuerzo)
    if (mostrarLonchera && dia !== 'sabado' && dia !== 'domingo') {
      html += renderLoncheraBloque(dia, loncheraData);
    }

    // Almuerzo (viernes no tiene)
    if (!esViernes && d.almuerzo) {
      html += renderMealBlock(d.almuerzo, 'almuerzo', dia);
    } else if (esViernes) {
      html += `<div class="meal-block viernes-libre">
        <div class="meal-type-badge">🍽️ Almuerzo</div>
        <p class="viernes-libre-msg">La cocinera decide según lo que queda en el refrigerador.</p>
      </div>`;
    }

    html += `</div>`;
  });

  html += '</div>';
  container.innerHTML = html;
}

// ── RENDER COMPRAS ────────────────────────────────────────────
function renderCompras(data) {
  const container = document.getElementById('compras-container');
  if (!container) return;
  const CATS = {
    carnes_y_proteinas: '🥩 Carnes y proteínas',
    vegetales_y_frutas: '🥦 Vegetales y frutas',
    lacteos_y_huevos:   '🥚 Lácteos y huevos',
    despensa:           '🧂 Despensa',
  };
  function buildCard(lista, titulo, subtitulo, iconClass) {
    if (!lista) return '';
    let body = '';
    Object.entries(CATS).forEach(([k, label]) => {
      const items = lista[k] || [];
      if (!items.length) return;
      body += `<div class="categoria-title">${label}</div>`;
      body += `<ul class="compras-list">${items.map(i=>`<li class="compras-item">${escHtml(i)}</li>`).join('')}</ul>`;
    });
    if (!body) return '';
    const desc = lista.descripcion ? `<p style="font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-2)">${escHtml(lista.descripcion)}</p>` : '';
    return `<div class="compras-card">
      <div class="compras-header">
        <div class="compras-icon ${iconClass}">${iconClass==='domingo'?'🛒':'🏪'}</div>
        <div><div class="compras-title">${titulo}</div><div class="compras-subtitle">${subtitulo}</div>${desc}</div>
      </div>
      <div class="compras-body">${body}</div>
    </div>`;
  }
  container.innerHTML = `<div class="compras-grid">
    ${buildCard(data.lista_compras_domingos,'Compra del Domingo','Para lunes–jueves','domingo')}
    ${buildCard(data.lista_compras_mitad_semana,'Compra a Mitad de Semana','Para sábado–domingo','mitad')}
  </div>`;
}

// ── LOAD MENU ─────────────────────────────────────────────────
let menuData = null;

async function loadMenu() {
  const container    = document.getElementById('menu-container');
  const semanaLabel  = document.getElementById('semana-label');
  const semanaLabelC = document.getElementById('semana-label-compras');

  container.innerHTML = `<div class="loader-box"><div class="spinner"></div><p>Cargando menú…</p></div>`;
  showWakeBanner(container);

  try {
    const [res, lonchera] = await Promise.all([
      fetchConRetry(`${API}/menu-actual`, container),
      cargarLonchera()
    ]);
    clearWakeBanner(container);
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    menuData     = data;
    loncheraData = lonchera;
    if (semanaLabel)  semanaLabel.textContent  = data.semana || '';
    if (semanaLabelC) semanaLabelC.textContent = data.semana || '';
    renderMenu(data, container, true);
    renderCompras(data);
  } catch (err) {
    clearWakeBanner(container);
    container.innerHTML = `<div class="loader-box">
      <p>⚠️ No se pudo cargar el menú.</p>
      <p style="font-size:var(--text-xs);color:var(--color-text-faint);margin-top:.5rem">${escHtml(err.message)}</p>
      <button class="btn-primary" style="width:auto;margin-top:1rem" onclick="loadMenu()">Reintentar</button>
    </div>`;
    console.error('[Paca] loadMenu:', err);
  }
}

// ── LOAD MENÚ ANTERIOR ────────────────────────────────────────
let menuAnteriorCargado = false;

async function loadMenuAnterior() {
  if (menuAnteriorCargado) return;
  const container = document.getElementById('menu-anterior-container');
  const label     = document.getElementById('semana-label-anterior');
  if (!container) return;

  container.innerHTML = `<div class="loader-box"><div class="spinner"></div><p>Cargando…</p></div>`;
  showWakeBanner(container);

  try {
    const res = await fetchConRetry(`${API}/menu-anterior`, container);
    clearWakeBanner(container);
    if (res.status === 404) {
      container.innerHTML = `<p class="empty">Aún no hay semana anterior guardada.</p>`;
      return;
    }
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    if (label) label.textContent = data.semana || '';
    renderMenu(data, container, false); // sin lonchera en el histórico
    menuAnteriorCargado = true;
  } catch (err) {
    clearWakeBanner(container);
    container.innerHTML = `<div class="loader-box">
      <p>⚠️ No se pudo cargar el menú anterior.</p>
      <button class="btn-primary" style="width:auto;margin-top:1rem"
        onclick="menuAnteriorCargado=false;loadMenuAnterior()">Reintentar</button>
    </div>`;
    console.error('[Paca] loadMenuAnterior:', err);
  }
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
    selectedTipos.has(val) ? selectedTipos.delete(val) : selectedTipos.add(val);
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
      DIAS_ES.forEach(dia => {
        const d = (menuData.dias||{})[dia];
        if (!d) return;
        const label = DIAS_LABEL[dia]||dia;
        ['desayuno','almuerzo'].forEach(comida => {
          const m = d[comida];
          if (!m?.nombre) return;
          sel.add(new Option(`${label} — ${m.nombre}`, `${dia}|${comida}|${m.nombre}`));
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
    if (selectedTipos.size === 0) { toast('Elige al menos un tipo de feedback'); return; }

    const payload = {
      quien: selectedQuien, tipos: [...selectedTipos],
      plato:       document.getElementById('sel-plato')?.value || null,
      ingrediente: document.getElementById('inp-ingrediente')?.value || null,
      cantidad:    document.getElementById('inp-cantidad')?.value || null,
      comentario:  document.getElementById('inp-comentario')?.value || null,
    };
    btn.disabled = true; btn.textContent = 'Enviando…';
    try {
      const res = await fetch(`${API}/feedback`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload), signal: AbortSignal.timeout(30000),
      });
      if (!res.ok) throw new Error((await res.text())||`Error ${res.status}`);
      toast('✅ Feedback enviado — se incorporará el próximo sábado 🙏');
      feedbackForm.reset(); selectedTipos.clear();
      document.querySelectorAll('#chips-tipo .chip').forEach(b=>b.classList.remove('active'));
      document.querySelectorAll('#chips-quien .chip').forEach(b=>b.classList.remove('active'));
      document.querySelector('#chips-quien .chip[data-val="Fernando"]')?.classList.add('active');
      selectedQuien = 'Fernando'; updateConditionalFields(); loadFeedbacks();
    } catch (err) {
      toast(`⚠️ Error: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Enviar feedback <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }
  });
}

// ── LOAD FEEDBACKS ────────────────────────────────────────────
const TIPO_LABELS = {
  no_gusto:'😕 No gustó', ingrediente:'🛒 Ingrediente difícil',
  cantidad:'⚖️ Cantidad incorrecta', comentario:'💬 Comentario libre',
};

async function loadFeedbacks() {
  const container = document.getElementById('historial-container');
  if (!container) return;
  container.innerHTML = `<div class="loader-box" style="padding:var(--space-6)"><div class="spinner"></div></div>`;
  try {
    const res = await fetch(`${API}/feedbacks`, { signal: AbortSignal.timeout(30000) });
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const items = await res.json();
    if (!items.length) { container.innerHTML = `<p class="empty">Aún no hay feedbacks esta semana.</p>`; return; }
    container.innerHTML = [...items].reverse().map(fb => {
      const tipos = (fb.tipos||[]).map(t=>`<span class="fb-tipo-badge">${TIPO_LABELS[t]||t}</span>`).join('');
      const extras = [
        fb.plato       ? `Plato: ${escHtml(fb.plato.split('|').pop())}` : null,
        fb.ingrediente ? `Ingrediente: ${escHtml(fb.ingrediente)}`       : null,
        fb.cantidad    ? `Cantidad: ${escHtml(fb.cantidad)}`             : null,
      ].filter(Boolean).join(' · ');
      const comentario = fb.comentario || extras;
      return `<div class="fb-item">
        <div class="fb-meta"><span class="fb-quien">${escHtml(fb.quien)}</span><span class="fb-fecha">${formatFecha(fb.fecha)}</span></div>
        <div class="fb-tipos">${tipos}</div>
        ${comentario ? `<p class="fb-comentario">${escHtml(comentario)}</p>` : ''}
      </div>`;
    }).join('');
  } catch (err) {
    container.innerHTML = `<p class="empty">No se pudo cargar el historial.</p>`;
  }
}

// ── LOAD MEMORIA ──────────────────────────────────────────────
async function loadMemoria() {
  const container = document.getElementById('memoria-container');
  if (!container) return;
  container.innerHTML = `<div class="loader-box" style="padding:var(--space-6)"><div class="spinner"></div></div>`;
  try {
    const res = await fetchConRetry(`${API}/memoria`, container);
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    const reglas = data.reglas_permanentes || [];
    const historial = data.historial_feedbacks || [];

    if (!reglas.length && !historial.length) {
      container.innerHTML = `<p class="empty">La memoria se construye automáticamente con el feedback de cada semana.</p>`;
      return;
    }

    let html = '';
    if (reglas.length) {
      html += `<div class="memoria-section">
        <h3 class="memoria-title">📌 Reglas permanentes (${reglas.length})</h3>
        <ul class="memoria-list">${reglas.map(r=>`<li class="memoria-item">${escHtml(r)}</li>`).join('')}</ul>
      </div>`;
    }
    if (historial.length) {
      html += `<div class="memoria-section" style="margin-top:var(--space-6)">
        <h3 class="memoria-title">📋 Historial de feedbacks incorporados</h3>
        ${[...historial].reverse().map(h=>`<div class="fb-item">
          <div class="fb-meta"><span class="fb-quien">${escHtml(h.semana||'')}</span><span class="fb-fecha">${h.feedbacks_count||0} feedbacks</span></div>
          <p class="fb-comentario">${escHtml(h.resumen||'')}</p>
          ${(h.reglas_agregadas||[]).length ? `<div class="fb-tipos">${h.reglas_agregadas.map(r=>`<span class="fb-tipo-badge">+${escHtml(r.slice(0,50))}…</span>`).join('')}</div>` : ''}
        </div>`).join('')}
      </div>`;
    }
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<p class="empty">No se pudo cargar la memoria.</p>`;
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
    if (!texto) { toast('Escribe la lonchera antes de guardar'); return; }
    btn.disabled = true; btn.textContent = 'Guardando…';
    try {
      const res = await fetch(`${API}/lonchera`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({texto}), signal: AbortSignal.timeout(30000),
      });
      if (!res.ok) throw new Error((await res.text())||`Error ${res.status}`);
      toast('✅ Lonchera guardada correctamente');
      loncheraData = null; input.value = '';
    } catch (err) {
      toast(`⚠️ Error: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Guardar lonchera <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }
  });
}

// ── INIT ──────────────────────────────────────────────────────
loadMenu();
