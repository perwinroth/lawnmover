const CATEGORY_COLORS = {
  // Lawn mower sellers
  robot_mower_seller: '#2c7fb8',
  // Legacy categories (kept for compatibility)
  national_park: '#2ca25f',
  nature_reserve: '#99d8c9',
  camp_site: '#fb6a4a',
  shelter: '#ef3b2c',
  viewpoint: '#8856a7',
  picnic_site: '#9ebcda',
  slipway: '#3182bd',
  canoe_kayak: '#41b6c4',
  boat_rental: '#0868ac',
};

const CATEGORY_LABELS = {
  robot_mower_seller: 'Återförsäljare robotgräsklippare',
  national_park: 'Nationalpark',
  nature_reserve: 'Naturreservat',
  camp_site: 'Camping',
  shelter: 'Vindskydd / Shelter',
  viewpoint: 'Utsiktsplats',
  picnic_site: 'Picknick',
  slipway: 'Båtramp / Slip',
  canoe_kayak: 'Kanot / Kajak',
  boat_rental: 'Båt/Kanot-uthyrning',
};

function iconFor(cat, size=12) {
  const map = {
    national_park: 'hiking',
    nature_reserve: 'hiking',
    camp_site: 'camp_site',
    shelter: 'shelter',
    viewpoint: 'viewpoint',
    picnic_site: 'picnic_site',
    slipway: 'slipway',
    canoe_kayak: 'canoe_kayak',
    boat_rental: 'boat_rental',
  };
  const key = map[cat] || 'hiking';
  const src = `icons/${key}.svg`;
  return `<img src="${src}" alt="" width="${size}" height="${size}" style="vertical-align:middle; margin-right:6px"/>`;
}

// State
let ACTIVE_CATS = new Set(Object.keys(CATEGORY_COLORS));
let ITEMS = new Map(); // id -> {id, name, link, cats, lat, lng}
let MARKER_BY_ID = new Map(); // id -> marker
let THE_MAP = null;
let CLUSTER = null; // marker cluster group
let ALL_MARKERS = []; // markers for all items
let SEARCH_QUERY = '';

function initMap() {
  const map = L.map('map').setView([62.0, 15.0], 5); // Sweden
  THE_MAP = map;

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map);

  // Cluster group for all markers
  CLUSTER = L.markerClusterGroup({
    disableClusteringAtZoom: 14,
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
    maxClusterRadius: 50,
  });
  map.addLayer(CLUSTER);

  buildFilters(map);
  buildChips();
  buildSearch();
  loadData(map);
}

function buildFilters(map) {
  const container = document.getElementById('filters');
  container.innerHTML = '';
  Object.entries(CATEGORY_LABELS).forEach(([key, label]) => {
    const id = `filter-${key}`;
    const wrap = document.createElement('div');
    wrap.className = 'filter-item';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = id;
    checkbox.checked = true;
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) ACTIVE_CATS.add(key);
      else ACTIVE_CATS.delete(key);
      applyFilter();
      renderList();
    });

    const color = document.createElement('span');
    color.className = 'color';
    color.style.backgroundColor = CATEGORY_COLORS[key];

    const labelEl = document.createElement('label');
    labelEl.htmlFor = id;
    labelEl.textContent = label;

    wrap.appendChild(checkbox);
    wrap.appendChild(color);
    wrap.appendChild(labelEl);
    container.appendChild(wrap);
  });
}

function markerFor(cats, feature, latLng) {
  const cat = (cats && cats[0]) || 'other';
  const color = CATEGORY_COLORS[cat] || '#444';
  const icon = L.divIcon({
    className: 'dot',
    html: `<span style="background:${color}"></span>`,
    iconSize: [12, 12],
  });
  return L.marker(latLng, { icon });
}

function popupHtml(props) {
  const name = props.name || '(namnlös)';
  const link = props.link || props.osm_url;
  const cats = (props.categories || []).map((c) => CATEGORY_LABELS[c] || c).join(', ');
  const book = props.bookable ? ' • Bokningsbar' : '';
  const safeLink = link ? `<a href="${link}" target="_blank" rel="noopener">${props.bookable ? 'Boka' : 'Länk'}</a>` : '';
  const icon = (props.categories && props.categories[0]) ? iconFor(props.categories[0], 14) : '';
  const linkBadge = (typeof props.link_ok === 'boolean') ? `<span class="badge ${props.link_ok ? 'ok' : 'err'}" style="margin-left:6px">${props.link_ok ? 'Länk OK' : 'Länk fel'}</span>` : '';
  const openBadge = (typeof props.open_now === 'boolean') ? `<span class="badge ${props.open_now ? 'ok' : 'warn'}" style="margin-left:6px">${props.open_now ? 'Öppet' : 'Stängt'}</span>` : '';
  return `
    <div class="popup">
      <strong>${icon}${name}</strong> ${openBadge} ${linkBadge}<br/>
      <small>${cats}${book}</small><br/>
      ${safeLink}
    </div>
  `;
}

async function loadData(map) {
  try {
    const res = await fetch('../data/lawnmover.geojson');
    const geo = await res.json();
    buildItems(geo);
    renderData(map, geo);
    applyFilter();
    renderList();
  } catch (e) {
    console.error('Failed to load data', e);
    const el = document.createElement('div');
    el.className = 'error';
    el.textContent = 'Kunde inte ladda data. Har du kört skripten?';
    document.getElementById('controls').appendChild(el);
  }
}

function renderData(map, geo) {
  ALL_MARKERS = [];
  MARKER_BY_ID = new Map();
  (geo.features || []).forEach((f) => {
    const [lng, lat] = f.geometry.coordinates;
    const props = f.properties || {};
    const cats = props.categories || [];
    const m = markerFor(cats, f, [lat, lng]).bindPopup(popupHtml(props));
    m.__cats = new Set(cats);
    m.__id = props.id;
    m.__name = (props.name || '').toLowerCase();
    ALL_MARKERS.push(m);
    MARKER_BY_ID.set(props.id, m);
  });
}

function applyFilter() {
  if (!CLUSTER) return;
  CLUSTER.clearLayers();
  const filtered = ALL_MARKERS.filter((m) => {
    let catOK = false;
    for (const c of m.__cats) if (ACTIVE_CATS.has(c)) { catOK = true; break; }
    if (!catOK) return false;
    if (!SEARCH_QUERY) return true;
    return m.__name && m.__name.includes(SEARCH_QUERY);
  });
  CLUSTER.addLayers(filtered);
}

document.addEventListener('DOMContentLoaded', initMap);
// Default view classes
window.addEventListener('load', () => {
  if (window.innerWidth <= 900) {
    document.body.classList.add('show-list');
  }
  const navMap = document.getElementById('navMap');
  const navList = document.getElementById('navList');
  if (navMap) navMap.addEventListener('click', (e) => { e.preventDefault(); document.body.classList.remove('show-list'); document.body.classList.add('show-map'); });
  if (navList) navList.addEventListener('click', (e) => { e.preventDefault(); document.body.classList.remove('show-map'); document.body.classList.add('show-list'); });
});

function buildItems(geo) {
  ITEMS = new Map();
  (geo.features || []).forEach((f) => {
    const [lng, lat] = f.geometry.coordinates;
    const p = f.properties || {};
    ITEMS.set(p.id, {
      id: p.id,
      name: p.name || '(namnlös)'
        , link: p.link || p.osm_url,
      cats: p.categories || [],
      lat, lng,
      open_now: p.open_now,
      link_ok: p.link_ok,
    });
  });
}

function renderList() {
  const listEl = document.getElementById('list');
  if (!listEl) return;
  const active = ACTIVE_CATS;
  const q = SEARCH_QUERY;
  let items = Array.from(ITEMS.values()).filter((it) =>
    it.cats.some((c) => active.has(c)) && (!q || (it.name || '').toLowerCase().includes(q))
  );
  if (USER_POS) {
    items.forEach((it) => { it._dist = distanceKm(USER_POS.lat, USER_POS.lon, it.lat, it.lng); });
    items.sort((a, b) => (a._dist || Infinity) - (b._dist || Infinity));
  } else {
    items.sort((a, b) => a.name.localeCompare(b.name, 'sv'));
  }
  const html = [
    `<div class="meta" style="padding:4px 8px; color:#666;">${items.length} platser${USER_POS ? ' – sorterat efter avstånd' : ''}</div>`
  ];
  items.forEach((it) => {
    const slug = slugify(it.id);
    const q = SEARCH_QUERY;
    const nameHtml = q ? highlightName(it.name, q) : escapeHTML(it.name);
    const badges = it.cats
      .filter((c) => active.has(c))
      .map((c) => `<span class="badge" style="background:${CATEGORY_COLORS[c]};display:inline-flex;align-items:center;gap:6px">${iconFor(c,12)}${CATEGORY_LABELS[c] || c}</span>`)
      .join(' ');
    const safeLink = it.link ? `<a href="${it.link}" target="_blank" rel="noopener">Länk</a>` : '';
    const dist = (USER_POS && typeof it._dist === 'number') ? ` <small style="color:#64748b">${it._dist.toFixed(1)} km</small>` : '';
    const openBadge = (typeof it.open_now === 'boolean') ? `<span class=\"badge ${it.open_now ? 'ok' : 'warn'}\">${it.open_now ? 'Öppet' : 'Stängt'}</span>` : '';
    const linkBadge = (typeof it.link_ok === 'boolean') ? `<span class=\"badge ${it.link_ok ? 'ok' : 'err'}\">${it.link_ok ? 'Länk OK' : 'Länk fel'}</span>` : '';
    html.push(`
      <div class=\"list-item\" data-id=\"${it.id}\">\n        <div class=\"name\">${it.cats && it.cats[0] ? iconFor(it.cats[0],14) : ''}<a href=\"places/${slug}.html\">${nameHtml}</a>${dist} ${openBadge} ${linkBadge} ${it.bookable ? '<span class=\\"badge\\" style=\\"background:#0f766e\\">Boka</span>' : ''}</div>\n        <div class=\"meta\">${badges} ${safeLink}</div>\n      </div>
    `);
  });
  listEl.innerHTML = html.join('\n');

  listEl.querySelectorAll('.list-item').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-id');
      const it = ITEMS.get(id);
      if (!it) return;
      showDetails(it, it.lat, it.lng);
      if (window.innerWidth <= 900) { document.body.classList.remove('show-list'); document.body.classList.add('show-map'); }
      THE_MAP.setView([it.lat, it.lng], Math.max(12, THE_MAP.getZoom()));
      const m = MARKER_BY_ID.get(id);
      if (m && CLUSTER) {
        CLUSTER.zoomToShowLayer(m, () => m.openPopup());
      } else if (m) {
        m.openPopup();
      }
    });
  });
}

function showDetails(props, lat, lng) {
  const el = document.getElementById('details');
  if (!el) return;
  const icon = (props.cats && props.cats[0]) ? iconFor(props.cats[0], 16) : ((props.categories && props.categories[0]) ? iconFor(props.categories[0],16) : '');
  const name = escapeHTML(props.name || '(namnlös)');
  const cats = (props.cats || props.categories || []).map((c) => escapeHTML(CATEGORY_LABELS[c] || c)).join(', ');
  const link = props.link || props.osm_url;
  const openBadge = (typeof props.open_now === 'boolean') ? `<span class=\"badge ${props.open_now ? 'ok' : 'warn'}\">${props.open_now ? 'Öppet' : 'Stängt'}</span>` : '';
  const linkBadge = (typeof props.link_ok === 'boolean') ? `<span class=\"badge ${props.link_ok ? 'ok' : 'err'}\">${props.link_ok ? 'Länk OK' : 'Länk fel'}</span>` : '';
  const rows = [];
  rows.push(`<div class=\"row\">${cats} ${openBadge} ${linkBadge}</div>`);
  rows.push(`<div class=\"row\">Koordinater: ${lat?.toFixed ? lat.toFixed(5) : lat}, ${lng?.toFixed ? lng.toFixed(5) : lng}</div>`);
  el.innerHTML = `
    <div class=\"title\">${icon}${name}</div>
    ${rows.join('')}
    <div class=\"actions\">
      ${link ? `<a class=\"btn\" href=\"${link}\" target=\"_blank\" rel=\"noopener\">Besök webbplats</a>` : ''}
    </div>
  `;
}

// Category chips in the search area
function setCatActive(cat, active) {
  if (active) ACTIVE_CATS.add(cat); else ACTIVE_CATS.delete(cat);
  // Sync checkbox if present
  const cb = document.getElementById(`filter-${cat}`);
  if (cb) cb.checked = ACTIVE_CATS.has(cat);
  // Sync chip active state
  const chip = document.querySelector(`.chip[data-cat="${cat}"]`);
  if (chip) chip.classList.toggle('active', ACTIVE_CATS.has(cat));
}

function buildChips() {
  const el = document.getElementById('chips');
  if (!el) return;
  el.innerHTML = '';
  Object.entries(CATEGORY_LABELS).forEach(([key, label]) => {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.dataset.cat = key;
    chip.classList.toggle('active', ACTIVE_CATS.has(key));
    const dot = document.createElement('span');
    dot.className = 'dot';
    dot.style.backgroundColor = CATEGORY_COLORS[key];
    const text = document.createElement('span');
    text.textContent = label;
    chip.appendChild(dot);
    chip.appendChild(text);
    chip.addEventListener('click', () => {
      const willActivate = !ACTIVE_CATS.has(key);
      setCatActive(key, willActivate);
      applyFilter();
      renderList();
    });
    el.appendChild(chip);
  });
}

// Search UI
function debounce(fn, ms) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function buildSearch() {
  const input = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearch');
  if (!input) return;
  const onChange = debounce(() => {
    SEARCH_QUERY = (input.value || '').trim().toLowerCase();
    if (clearBtn) clearBtn.hidden = SEARCH_QUERY.length === 0;
    applyFilter();
    renderList();
  }, 150);
  input.addEventListener('input', onChange);
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      SEARCH_QUERY = '';
      clearBtn.hidden = true;
      applyFilter();
      renderList();
      input.focus();
    });
  }
}

// Helpers for safe highlighting
function escapeHTML(s) {
  return (s || '').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
}

function highlightName(name, q) {
  const source = String(name || '');
  const lower = source.toLowerCase();
  const query = String(q || '').toLowerCase();
  if (!query) return escapeHTML(source);
  let i = 0;
  let res = '';
  while (true) {
    const idx = lower.indexOf(query, i);
    if (idx === -1) {
      res += escapeHTML(source.slice(i));
      break;
    }
    res += escapeHTML(source.slice(i, idx));
    res += '<span class="hl">' + escapeHTML(source.slice(idx, idx + query.length)) + '</span>';
    i = idx + query.length;
  }
  return res;
}

function slugify(s) {
  return String(s || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'plats';
}
