"""The journey player: a self-contained client-side cinematic map animation.

MapLibre GL JS is vendored locally (assets/vendor) and inlined into the
component, so the player itself works offline; the basemap needs internet —
a stylized dark VECTOR basemap (OpenFreeMap tiles: water, parks, roads, rail,
3D building extrusions) with automatic fallback to the raster Carto style if
vector tiles cannot load. All playback state lives inside the component;
Streamlit only supplies the ordered journey data.

Cinematic design ("watching my life unfold"):
- Three camera altitudes, one continuous camera: wide overhead between
  regions, regional framing during travel, and a tilted street-level 3D
  arrival at the venue (when its coordinate is distance-validated).
- Travel is animated by inferred mode — airplane (with contrail), car, ship
  for the cruise, walking — along an eased path; never an instant jump.
- Arrival is a sequence: ease toward the venue, street labels appear with
  the zoom, the marker warms to a glow, an optional small crowd gathers
  (only when attendance metadata exists), and the camera drifts in a slow
  orbit while the ticket holds.
- Seasons tint the scene from the concert date; repeated segments thicken
  into memory trails; the finished route stays visible like a travel diary.
- Calm throughout: no badges, scores, particles, or hard cuts. Reduced
  motion disables travel/orbit animation but keeps every function working.
"""
from __future__ import annotations

import json

import streamlit as st

from src.config import ASSETS_DIR

VENDOR = ASSETS_DIR / "vendor"

ROUTE_SENTENCE = "Your route through these shows — the order you attended them, not the artist's tour."

PLAYER_CSS = """
  html,body { margin:0; padding:0; background:#0c1012; font-family:-apple-system,'Segoe UI',Roboto,sans-serif; }
  #wrap { position:relative; width:100%; height:__MAP_H__px; border-radius:3px; overflow:hidden; }
  #map { position:absolute; inset:0; }
  /* Seasonal atmosphere: one quiet tint layer, never a weather simulation. */
  #season { position:absolute; inset:0; pointer-events:none; z-index:3; transition:background 1.2s ease; }
  #season.winter { background:linear-gradient(180deg, rgba(140,170,210,.10), rgba(10,14,22,.16)); }
  #season.spring { background:linear-gradient(180deg, rgba(120,200,130,.05), transparent 70%); }
  #season.summer { background:linear-gradient(180deg, rgba(255,200,120,.05), transparent 70%); }
  #season.fall   { background:linear-gradient(180deg, rgba(230,140,60,.07), rgba(30,18,8,.08)); }
  #overlay { position:absolute; top:12px; left:12px; z-index:5; width:min(330px, 78vw); pointer-events:none; }
  #jtitle { color:#eee7da; font-weight:850; font-size:1.05rem; letter-spacing:.06em; text-transform:uppercase;
            text-shadow:0 1px 8px rgba(0,0,0,.85); }
  #jsub { color:#e89a3d; font-size:.7rem; letter-spacing:.18em; text-transform:uppercase; font-weight:800;
          margin-bottom:.55rem; text-shadow:0 1px 6px rgba(0,0,0,.85); font-variant-numeric:tabular-nums; }
  #card { pointer-events:auto; filter:drop-shadow(0 2px 3px rgba(0,0,0,.45)); }

  .jticket { display:flex; position:relative; align-items:stretch;
             background:
               repeating-linear-gradient(90deg, rgba(74,58,30,.028) 0 1px, transparent 1px 4px),
               radial-gradient(ellipse 120% 90% at 78% 8%, rgba(140,112,62,.12), transparent 60%),
               radial-gradient(ellipse 100% 120% at 0% 100%, rgba(120,95,50,.08), transparent 55%),
               linear-gradient(168deg,#f1e7d3 0%, #ecdfc6 60%, #e5d6b8 100%);
             color:#1c1710; border-radius:1px; overflow:hidden;
             border:1px solid rgba(58,45,22,.5); box-shadow:0 3px 14px rgba(0,0,0,.5); }
  .jt-stubwrap { flex:0 0 4.2rem; display:flex; align-items:stretch; position:relative; }
  .jt-date { flex:1; text-align:center; padding:.5rem .25rem; display:flex; flex-direction:column;
             justify-content:center; }
  .jt-year { font-size:1.45rem; font-weight:850; line-height:1; font-variant-numeric:tabular-nums; }
  .jt-rule { width:70%; margin:.28rem auto; border-top:1px solid rgba(58,45,22,.4); }
  .jt-md { font-size:.66rem; letter-spacing:.18em; font-weight:800; color:#5d5138; }
  .jt-perf { flex:0 0 6px; position:relative;
             background-image:radial-gradient(circle, rgba(28,23,16,.5) 1.4px, transparent 1.6px);
             background-size:6px 8px; background-repeat:repeat-y; background-position:center; }
  .jt-main { padding:.5rem .65rem .45rem; min-width:0; flex:1; position:relative; }
  .jt-head { font-size:.52rem; letter-spacing:.26em; text-transform:uppercase; color:#9a8c6a; font-weight:700; }
  .jt-t { font-weight:850; font-size:1rem; text-transform:uppercase; line-height:1.12; margin-top:.06rem; }
  .jt-venue { font-size:.8rem; font-weight:750; color:#33291a; margin-top:.14rem; }
  .jt-city { font-size:.72rem; color:#5d5138; }
  .jt-also { font-size:.64rem; color:#6b5f45; margin-top:.22rem; border-top:1px solid rgba(58,45,22,.25);
             padding-top:.2rem; }
  .jt-also b { font-weight:800; letter-spacing:.1em; color:#8a7c5c; }
  .jt-meta { font-size:.64rem; color:#8a7c5c; margin-top:.2rem; font-weight:800; letter-spacing:.1em; }
  .jt-mile { font-size:.66rem; color:#7c6a48; margin-top:.12rem; font-style:italic; }
  .jt-note { color:#a34a37; font-weight:800; }
  .jt-stamp { position:absolute; top:.35rem; right:.45rem; color:rgba(163,74,55,.62);
              border:1.5px solid rgba(163,74,55,.5); border-radius:1px; padding:.06rem .3rem;
              font-size:.52rem; font-weight:850; letter-spacing:.2em; transform:rotate(-4deg); }

  #controls { background:#111719; border:1px solid #343a3b; border-top:none; border-radius:0 0 3px 3px;
              padding:.55rem .8rem .65rem; color:#eee7da; }
  #cbar { display:flex; align-items:center; gap:.55rem; flex-wrap:wrap; }
  #controls button { background:#1a2124; color:#eee7da; border:1px solid #343a3b; border-radius:2px;
              padding:.32rem .7rem; font-size:.78rem; font-weight:700; letter-spacing:.08em; cursor:pointer; }
  #controls button:hover { border-color:#e89a3d; }
  #controls button:focus-visible { outline:2px solid #e89a3d; outline-offset:1px; }
  #controls button.primary { background:#e89a3d; color:#241d12; border-color:#e89a3d; }
  #controls button[aria-pressed="true"] { border-color:#e89a3d; color:#e89a3d; }
  #counter { font-variant-numeric:tabular-nums; font-size:.78rem; color:#a6aaa7; margin-left:auto; }
  #scrub { width:100%; accent-color:#e89a3d; margin-top:.45rem; }
  #route-note { color:#a6aaa7; font-size:.68rem; letter-spacing:.04em; margin-top:.3rem; }

  /* REGRESSION GUARD — do not change this structure:
     MapLibre owns the inline `transform` on marker roots (.lemarker, .veh,
     .crowdwrap). Never animate or overwrite transform on a marker root;
     all visuals (scale, pulse, glow, ring, rotation) belong to inner
     elements (.dot, .veh-icon, .crowd-dot) only. */
  .lemarker { position:relative; }
  .lemarker .dot { position:absolute; inset:0; border-radius:50%;
              border:1px solid rgba(238,231,218,.45); transition:box-shadow .8s ease; }
  .lemarker .cnt { position:absolute; top:-9px; right:-9px; background:#241d12; color:#e89a3d;
              border:1px solid #e89a3d; border-radius:8px; font-size:9px; font-weight:800;
              padding:0 4px; line-height:13px; z-index:1; }
  .lemarker.current .dot { border:2px solid #f7e8c9; }
  .lemarker.arrived .dot { box-shadow:0 0 22px 7px rgba(240,178,100,.75) !important; }
  @keyframes lepulse { 0%{transform:scale(1)} 50%{transform:scale(1.5)} 100%{transform:scale(1)} }
  .lemarker.current.pulse .dot { animation:lepulse 1.1s ease-in-out infinite; }
  @media (prefers-reduced-motion: reduce) { .lemarker.current.pulse .dot { animation:none; } }

  .veh { position:relative; }
  .veh .veh-icon { position:absolute; left:50%; top:50%; width:22px; height:22px; margin:-11px 0 0 -11px;
        filter:drop-shadow(0 0 4px rgba(0,0,0,.7)); }
  .veh .veh-icon svg { width:100%; height:100%; }
  .crowdwrap { position:relative; }
  .crowd-dot { position:absolute; width:5px; height:5px; border-radius:50%; background:#d8c9a8;
        opacity:0; transition:transform 1.4s ease, opacity .9s ease; }

  @media (max-width: 700px) {
    #overlay { position:static; width:auto; padding:.5rem .6rem 0; }
    #jtitle, #jsub { text-shadow:none; }
    #wrap { height:__MAP_NARROW_H__px; }
  }
"""

HEADER_JS = """
function headerCount(n) { return n + (n === 1 ? ' TIME SEEN' : ' TIMES SEEN'); }
function headerSpan(firstYear, currentYear) {
  return firstYear === currentYear ? String(firstYear) : firstYear + '\\u2013' + currentYear;
}
function headerLine(stops, i) {
  const y0 = Number(stops[0].event_date.slice(0, 4));
  let yc = y0;
  for (let k = 1; k <= i; k++) yc = Math.max(yc, Number(stops[k].event_date.slice(0, 4)));
  return headerCount(i + 1) + ' \\u00b7 ' + headerSpan(y0, yc);
}
"""

PLAYER_JS = """
const RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const N = STOPS.length;
let idx = 0, playing = false, speed = 1, raf = null, cineCam = false, playToken = 0;

const withCoords = STOPS.filter(s => s.has_coords);
function coordKey(s) { return s.latitude.toFixed(6) + ',' + s.longitude.toFixed(6); }

const TOTALS = {};
withCoords.forEach(s => { const k = coordKey(s); TOTALS[k] = (TOTALS[k] || 0) + 1; });
const MAXTOT = Math.max(1, ...Object.values(TOTALS));
function gravity(k) { return Math.sqrt((TOTALS[k] || 1) / MAXTOT); }
function gravityColor(t) {
  const r = Math.round(243 + (198-243)*t), g = Math.round(217 + (86-217)*t), b = Math.round(167 + (16-167)*t);
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}

// ---- Basemaps: stylized dark vector world (3D-capable) with raster fallback.
const RASTER_STYLE = { version: 8, sources: { carto: { type:'raster',
  tiles:['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
         'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
         'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
  tileSize:256, attribution:'&copy; OpenStreetMap contributors &copy; CARTO' } },
  layers: [{ id:'base', type:'raster', source:'carto' }] };

const SEASON_PARK = { winter:'#182026', spring:'#17301e', summer:'#153524', fall:'#2c2413' };

const VEC_STYLE = { version: 8,
  glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
  sources: { ofm: { type:'vector', url:'https://tiles.openfreemap.org/planet' } },
  layers: [
    { id:'bg', type:'background', paint:{ 'background-color':'#10151a' } },
    { id:'park', type:'fill', source:'ofm', 'source-layer':'park',
      paint:{ 'fill-color':'#17301e', 'fill-opacity':0.6 } },
    { id:'water', type:'fill', source:'ofm', 'source-layer':'water',
      paint:{ 'fill-color':'#0a1a26' } },
    { id:'waterway', type:'line', source:'ofm', 'source-layer':'waterway',
      paint:{ 'line-color':'#0a1a26', 'line-width':1.4 } },
    { id:'roads-minor', type:'line', source:'ofm', 'source-layer':'transportation', minzoom:12,
      filter:['in','class','minor','service','residential','tertiary'],
      paint:{ 'line-color':'#232b30', 'line-width':['interpolate',['linear'],['zoom'],12,0.4,16,3] } },
    { id:'roads-major', type:'line', source:'ofm', 'source-layer':'transportation',
      filter:['in','class','motorway','trunk','primary','secondary'],
      paint:{ 'line-color':'#39423f', 'line-width':['interpolate',['linear'],['zoom'],6,0.5,12,2,16,7] } },
    { id:'rail', type:'line', source:'ofm', 'source-layer':'transportation', minzoom:11,
      filter:['==','class','rail'],
      paint:{ 'line-color':'#3a3630', 'line-width':1, 'line-dasharray':[3,3] } },
    { id:'building', type:'fill-extrusion', source:'ofm', 'source-layer':'building', minzoom:13,
      paint:{ 'fill-extrusion-color':'#212a30',
              'fill-extrusion-height':['coalesce',['get','render_height'],6],
              'fill-extrusion-base':['coalesce',['get','render_min_height'],0],
              'fill-extrusion-opacity':0.85 } },
    { id:'street-labels', type:'symbol', source:'ofm', 'source-layer':'transportation_name', minzoom:14,
      layout:{ 'symbol-placement':'line', 'text-field':['coalesce',['get','name:latin'],['get','name']],
               'text-font':['Noto Sans Regular'], 'text-size':10.5 },
      paint:{ 'text-color':'#6f7671', 'text-halo-color':'#0c1012', 'text-halo-width':1.1 } },
    { id:'place-labels', type:'symbol', source:'ofm', 'source-layer':'place', maxzoom:14,
      filter:['in','class','city','town'],
      layout:{ 'text-field':['coalesce',['get','name:latin'],['get','name']],
               'text-font':['Noto Sans Regular'],
               'text-size':['interpolate',['linear'],['zoom'],4,10,10,14] },
      paint:{ 'text-color':'#8a8f8c', 'text-halo-color':'#0c1012', 'text-halo-width':1.2 } }
  ] };

let STREET_OK = true;   // false once we fall back to raster (no extrusions/pitch)
const map = new maplibregl.Map({ container:'map', attributionControl:{compact:true},
  style: VEC_STYLE, center:[-95,39], zoom:3, keyboard:false, maxPitch:60 });
map.addControl(new maplibregl.NavigationControl({showCompass:false}), 'top-right');
map.on('error', e => {
  const src = e && e.sourceId;
  if (STREET_OK && (src === 'ofm' || (e.error && /glyphs|vector|style/i.test(String(e.error.message))))) {
    STREET_OK = false;
    map.setStyle(RASTER_STYLE);   // overlays re-attach on style.load below
  }
});

function fullBounds() {
  if (!withCoords.length) return null;
  const b = new maplibregl.LngLatBounds();
  withCoords.forEach(s => b.extend([s.longitude, s.latitude]));
  return b;
}
function boundsPadding() {
  const el = map.getContainer();
  const base = Math.max(40, Math.round(Math.min(el.clientWidth, el.clientHeight) * 0.10));
  const overlayPad = el.clientWidth >= 760 ? 360 : base;
  return { top: base + 20, bottom: base, right: base, left: overlayPad };
}
function fitAll(animate) {
  const b = fullBounds();
  if (b) map.fitBounds(b, { padding: boundsPadding(), pitch:0, bearing:0,
                            duration: (animate && !RM) ? 1200 : 0, maxZoom: 9 });
}

let markers = {};
let vehMarker = null, crowdMarker = null;

function routeCoordsUpTo(i) {
  const pts = [];
  for (let k = 0; k <= i; k++) {
    const s = STOPS[k];
    if (!s.has_coords) continue;
    const p = [s.longitude, s.latitude];
    if (!pts.length || pts[pts.length-1][0] !== p[0] || pts[pts.length-1][1] !== p[1]) pts.push(p);
  }
  return pts;
}
// Memory trails: repeated segments carry a count and render heavier, like
// worn paths through the map.
function trailFeatures(i) {
  const counts = {};
  const pts = [];
  for (let k = 0; k <= i; k++) {
    const s = STOPS[k];
    if (!s.has_coords) continue;
    const p = [s.longitude, s.latitude];
    if (pts.length && (pts[pts.length-1][0] !== p[0] || pts[pts.length-1][1] !== p[1])) {
      const a = pts[pts.length-1], b = p;
      const key = [a.join(','), b.join(',')].sort().join('|');
      counts[key] = counts[key] || { a:a, b:b, n:0 };
      counts[key].n += 1;
    }
    if (!pts.length || pts[pts.length-1][0] !== p[0] || pts[pts.length-1][1] !== p[1]) pts.push(p);
  }
  return { type:'FeatureCollection', features: Object.values(counts).map(c => (
    { type:'Feature', properties:{ n:c.n },
      geometry:{ type:'LineString', coordinates:[c.a, c.b] } })) };
}
function setLine(id, coords) {
  const src = map.getSource(id);
  if (src) src.setData({type:'Feature', geometry:{type:'LineString', coordinates: coords}});
}

function esc(t) { const d = document.createElement('div'); d.textContent = t ?? ''; return d.innerHTML; }
function ordinal(n) { const s=['th','st','nd','rd'], v=n%100; return n+(s[(v-20)%10]||s[v]||s[0]); }

function milestone(s) {
  if (s.appearance_number > 1 && s.region_visit_number === 1 && s.state_region)
    return 'First ' + esc(s.state_region) + ' show';
  if (s.city_visit_number === 1 && s.city_name)
    return s.appearance_number === 1 ? '' : 'First ' + esc(s.city_name) + ' show';
  if (s.location_visit_number === 1 && s.venue_name)
    return 'First time at ' + esc(s.venue_name);
  if (s.days_since_prev !== null && s.days_since_prev >= 1095)
    return 'Return after ' + Math.floor(s.days_since_prev / 365) + ' years';
  if (s.city_visit_number > 1 && s.city_name)
    return ordinal(s.city_visit_number) + ' time in ' + esc(s.city_name);
  return '';
}
function alsoListed(s) {
  const title = (s.event_title || '').trim().toLowerCase();
  return s.bill.filter(b => b.trim().toLowerCase() !== title);
}

function renderCard(s) {
  const dt = new Date(s.event_date + 'T12:00:00');
  const mon = dt.toLocaleString('en-US', {month:'short'}).toUpperCase();
  const also = alsoListed(s);
  const mile = milestone(s);
  const status = s.is_upcoming ? 'UPCOMING' : 'ARCHIVED';
  const note = s.has_coords ? '' :
    '<div class="jt-meta jt-note">No mapped point \\u2014 the route continues from the previous location.</div>';
  document.getElementById('card').innerHTML =
    '<div class="jticket">' +
    '<div class="jt-stubwrap"><div class="jt-date">' +
      '<div class="jt-year">' + dt.getFullYear() + '</div><div class="jt-rule"></div>' +
      '<div class="jt-md">' + mon + ' ' + String(dt.getDate()).padStart(2,'0') + '</div>' +
    '</div></div><div class="jt-perf"></div>' +
    '<div class="jt-main"><span class="jt-stamp">' + status + '</span>' +
      '<div class="jt-head">My Concert Atlas</div>' +
      '<div class="jt-t">' + esc(s.event_title) + '</div>' +
      '<div class="jt-venue">' + esc(s.venue_name) + '</div>' +
      '<div class="jt-city">' + esc(s.city_name) + (s.state_region ? ', ' + esc(s.state_region) : '') + '</div>' +
      (also.length ? '<div class="jt-also"><b>ALSO LISTED:</b> ' + also.map(esc).join(' \\u00b7 ') + '</div>' : '') +
      '<div class="jt-meta">TIME #' + s.appearance_number + '</div>' +
      (mile ? '<div class="jt-mile">' + mile + '</div>' : '') + note +
    '</div></div>';
  if (CONFIG.label_mode === 'artist') {
    document.getElementById('jsub').textContent = headerLine(STOPS, s.appearance_number - 1);
  }
  document.getElementById('season').className = s.season || '';
  const parkColor = SEASON_PARK[s.season];
  if (STREET_OK && parkColor && map.getLayer('park'))
    map.setPaintProperty('park', 'fill-color', parkColor);
}

function styleMarker(m, key, isCurrent) {
  const t = gravity(key);
  const size = Math.round(12 + 5 * t);
  m.el.style.width = size + 'px';
  m.el.style.height = size + 'px';
  const dot = m.el.querySelector('.dot');
  dot.style.background = gravityColor(t);
  dot.style.boxShadow = '0 0 ' + (4 + 12*t) + 'px ' + (1 + 3*t) + 'px rgba(232,154,61,' + (0.25 + 0.45*t).toFixed(2) + ')';
  m.el.classList.toggle('current', isCurrent);
  m.el.classList.toggle('pulse', isCurrent && !RM);
  if (!isCurrent) m.el.classList.remove('arrived');
}

function rebuild(i, animate) {
  Object.values(markers).forEach(m => m.marker.remove());
  markers = {};
  const s = STOPS[i];
  for (let k = 0; k <= i; k++) {
    const st = STOPS[k];
    if (!st.has_coords) continue;
    const key = coordKey(st);
    if (!markers[key]) {
      const el = document.createElement('div');
      el.className = 'lemarker';
      el.innerHTML = '<div class="dot"></div><span class="cnt" style="display:none"></span>';
      const mk = new maplibregl.Marker({element: el}).setLngLat([st.longitude, st.latitude]).addTo(map);
      markers[key] = {marker: mk, el: el, count: 0};
    }
    markers[key].count += 1;
  }
  let currentKey = null;
  if (s.has_coords) currentKey = coordKey(s);
  else for (let k = i; k >= 0; k--) if (STOPS[k].has_coords) { currentKey = coordKey(STOPS[k]); break; }
  Object.entries(markers).forEach(([key, m]) => {
    const c = m.el.querySelector('.cnt');
    if (m.count > 1) { c.style.display = 'block'; c.textContent = m.count; }
    styleMarker(m, key, key === currentKey);
  });

  const trails = map.getSource('trails');
  if (trails) trails.setData(trailFeatures(i));
  const coords = routeCoordsUpTo(i);
  if (coords.length >= 2 && s.has_coords && s.draw_segment_from_prev) {
    setLine('route-current', coords.slice(-2));
  } else {
    setLine('route-current', []);
  }

  renderCard(s);
  document.getElementById('counter').textContent = 'Show ' + (i+1) + ' of ' + N;
  document.getElementById('scrub').value = i;

  if (s.has_coords && !cineCam) {
    const pt = map.project([s.longitude, s.latitude]);
    const cv = map.getContainer();
    const pad = 70, padLeft = cv.clientWidth >= 760 ? 360 : pad;
    if (pt.x < padLeft || pt.y < pad || pt.x > cv.clientWidth - pad || pt.y > cv.clientHeight - pad) {
      RM ? map.jumpTo({center:[s.longitude, s.latitude]})
         : map.easeTo({center:[s.longitude, s.latitude], duration:800});
    }
  }
}

function show(i, animate) { idx = Math.max(0, Math.min(i, N-1)); rebuild(idx, animate); }

// ---------------------------------------------------------------- cinematics
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function easeAsync(opts) {
  if (RM) { map.jumpTo(opts); return Promise.resolve(); }
  return new Promise(res => { map.once('moveend', res); map.easeTo(opts); });
}
function currentToken() { return playToken; }

const VEH_SVG = {
  airplane: '<svg viewBox="0 0 24 24"><path fill="#e8d9b8" d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/></svg>',
  car: '<svg viewBox="0 0 24 24"><path fill="#e8d9b8" d="M5 11l1.5-4.5h11L19 11h1a1 1 0 0 1 1 1v4h-2a2 2 0 1 1-4 0H9a2 2 0 1 1-4 0H3v-4a1 1 0 0 1 1-1z"/></svg>',
  ship: '<svg viewBox="0 0 24 24"><path fill="#e8d9b8" d="M4 16l1.5-6H9V7h6v3h3.5L20 16c-1.5.8-3-.8-4.5 0s-3-.8-4.5 0-3 .8-4.5 0zM3 19c2 1 4-1 6 0s4-1 6 0 4-1 6 0v2c-2 1-4-1-6 0s-4-1-6 0-4 1-6 0z"/></svg>',
  walking: '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2.2" fill="#e8d9b8"/><path fill="#e8d9b8" d="M11 8h2l1 4 2.5 2-1 1.5-3-2.5-.5 3 2 5h-2l-2-4.5-1.5 4.5H6.5l2-6L9 12z"/></svg>'
};
function bearingBetween(a, b) {
  const pa = map.project(a), pb = map.project(b);
  return Math.atan2(pb.x - pa.x, pa.y - pb.y) * 180 / Math.PI;
}

// Travel: never an instant jump — a vehicle crosses the map, airplane legs
// leave a contrail, and the camera frames or follows the movement.
async function travelAnim(a, b, mode, distMi, token) {
  if (RM || !a || !b || !mode) return;
  const bb = new maplibregl.LngLatBounds(); bb.extend(a); bb.extend(b);
  const cam = map.cameraForBounds(bb, { padding: 110 });
  await easeAsync({ center: cam.center, zoom: Math.min(cam.zoom, mode === 'airplane' ? 8.5 : 11.5),
                    pitch: 0, bearing: 0, duration: 1000 / speed });
  if (token !== currentToken()) return;
  const el = document.createElement('div');
  el.className = 'veh';
  el.innerHTML = '<div class="veh-icon">' + (VEH_SVG[mode] || VEH_SVG.car) + '</div>';
  vehMarker = new maplibregl.Marker({ element: el }).setLngLat(a).addTo(map);
  const icon = el.querySelector('.veh-icon');   // rotation on the inner element only
  if (mode === 'airplane' || mode === 'ship') icon.style.transform = 'rotate(' + bearingBetween(a, b) + 'deg)';
  const dur = Math.min(3600, 1000 + (distMi || 50) * (mode === 'walking' ? 60 : 4)) / speed;
  const follow = (distMi || 0) > 600;
  const trail = [];
  await new Promise(res => {
    const t0 = performance.now();
    function frame(now) {
      if (token !== currentToken()) { res(); return; }
      const t = Math.min(1, (now - t0) / dur);
      const e = t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;   // ease-in-out
      const pos = [a[0] + (b[0]-a[0])*e, a[1] + (b[1]-a[1])*e];
      vehMarker.setLngLat(pos);
      if (mode === 'airplane') { trail.push(pos); setLine('contrail', trail); }
      if (follow) map.jumpTo({ center: pos });
      if (t < 1) raf = requestAnimationFrame(frame); else res();
    }
    raf = requestAnimationFrame(frame);
  });
  if (vehMarker) { vehMarker.remove(); vehMarker = null; }
  setLine('contrail', []);
}

// Arrival: ease toward the venue (street labels appear with the zoom), the
// marker warms to a glow, an optional small crowd gathers, and the camera
// drifts in a slow orbit while the ticket holds.
const CATEGORY_ZOOM = { club:16.2, theater:15.8, stadium:15.1, amphitheater:14.7, festival_grounds:14.5 };
const CROWD_SIZE = { solo:1, couple:2, friends:5, family:4, festival:16 };
async function arrivalAnim(s, token) {
  const hasVenue = s.venue_latitude !== null && s.venue_longitude !== null;
  const tgt = hasVenue ? [s.venue_longitude, s.venue_latitude] : [s.longitude, s.latitude];
  const zoom = STREET_OK ? (hasVenue ? (CATEGORY_ZOOM[s.venue_category] || 15.5) : 13.5)
                         : (hasVenue ? 13.5 : 12.5);
  const pitch = (STREET_OK && !RM) ? (hasVenue ? 55 : 42) : 0;
  await easeAsync({ center: tgt, zoom: zoom, pitch: pitch, duration: 1700 / speed });
  if (token !== currentToken()) return;
  const key = s.has_coords ? coordKey(s) : null;
  if (key && markers[key]) markers[key].el.classList.add('arrived');
  const k = CROWD_SIZE[s.attendance_type];
  if (k && !RM) {
    const el = document.createElement('div');
    el.className = 'crowdwrap';
    for (let c = 0; c < k; c++) {
      const d = document.createElement('div');
      d.className = 'crowd-dot';
      const ang = Math.random() * 6.283, r0 = 34 + Math.random() * 26, r1 = 8 + Math.random() * 8;
      d.style.transform = 'translate(' + (Math.cos(ang)*r0) + 'px,' + (Math.sin(ang)*r0) + 'px)';
      d.dataset.tx = 'translate(' + (Math.cos(ang)*r1) + 'px,' + (Math.sin(ang)*r1) + 'px)';
      el.appendChild(d);
    }
    crowdMarker = new maplibregl.Marker({ element: el }).setLngLat(tgt).addTo(map);
    requestAnimationFrame(() => el.querySelectorAll('.crowd-dot').forEach(d => {
      d.style.opacity = '0.85'; d.style.transform = d.dataset.tx;   // inner elements only
    }));
  }
  if (!RM) await easeAsync({ bearing: map.getBearing() + 16, duration: 1900 / speed,
                             easing: t => t });
  else await sleep(600);
  if (crowdMarker) {
    const cm = crowdMarker; crowdMarker = null;
    cm.getElement().querySelectorAll('.crowd-dot').forEach(d => d.style.opacity = '0');
    setTimeout(() => cm.remove(), 900);
  }
}

function lastCoordsBefore(i) {
  for (let k = i; k >= 0; k--) if (STOPS[k].has_coords) return [STOPS[k].longitude, STOPS[k].latitude];
  return null;
}

// The play loop: travel → arrive → hold, one stop at a time, chained (no
// fixed interval — each leg takes the time its journey needs).
async function runPlay(token) {
  while (playing && token === currentToken() && idx < N - 1) {
    const j = idx + 1, s = STOPS[j];
    const from = lastCoordsBefore(idx);
    const to = s.has_coords ? [s.longitude, s.latitude] : null;
    cineCam = true;
    if (from && to && (from[0] !== to[0] || from[1] !== to[1])) {
      await travelAnim(from, to, s.travel_mode, s.travel_miles, token);
    }
    if (!playing || token !== currentToken()) break;
    show(j, false);
    if (to) await arrivalAnim(s, token); else await sleep(1500 / speed);
    cineCam = false;
  }
  cineCam = false;
  if (playing && token === currentToken() && idx >= N - 1) finishJourney();
}

function finishJourney() { pause(); fitAll(true); }

const playBtn = document.getElementById('play');
function play() {
  if (N < 2) return;
  if (idx >= N-1) { cineCam = false; show(0, false); fitAll(false); }
  playing = true; playBtn.textContent = '\\u275a\\u275a Pause'; playBtn.classList.remove('primary');
  playToken += 1;
  runPlay(playToken);
}
function pause() {
  playing = false; playBtn.textContent = '\\u25ba Play Journey'; playBtn.classList.add('primary');
  playToken += 1;
  cineCam = false;
  if (raf) { cancelAnimationFrame(raf); raf = null; }
  if (vehMarker) { vehMarker.remove(); vehMarker = null; }
  setLine('contrail', []);
}
function toggle() { playing ? pause() : play(); }

document.getElementById('prev').onclick = () => { pause(); show(idx-1, false); };
document.getElementById('nextb').onclick = () => { pause(); if (idx < N-1) show(idx+1, true); };
playBtn.onclick = toggle;
document.getElementById('restart').onclick = () => { pause(); show(0, false); fitAll(false); };
document.querySelectorAll('[data-speed]').forEach(b => b.onclick = () => {
  speed = Number(b.dataset.speed);
  document.querySelectorAll('[data-speed]').forEach(x => x.setAttribute('aria-pressed', x === b));
});
const scrub = document.getElementById('scrub');
scrub.oninput = () => { pause(); show(Number(scrub.value), false); };
document.getElementById('wrap').addEventListener('keydown', e => {
  if (e.key === ' ') { e.preventDefault(); toggle(); }
  else if (e.key === 'ArrowRight') { pause(); if (idx < N-1) show(idx+1, true); }
  else if (e.key === 'ArrowLeft') { pause(); show(idx-1, false); }
  else if (e.key === 'Home') { pause(); show(0, false); }
});

function addOverlays() {
  if (!map.getSource('trails')) {
    map.addSource('trails', {type:'geojson', data:{type:'FeatureCollection', features:[]}});
    map.addLayer({ id:'trails-line', type:'line', source:'trails',
      paint:{ 'line-color':'#e89a3d',
              'line-width':['min', 4.5, ['+', 1.2, ['*', 0.9, ['-', ['get','n'], 1]]]],
              'line-opacity':['min', 0.7, ['+', 0.3, ['*', 0.08, ['get','n']]]] } });
  }
  if (!map.getSource('route-current')) {
    map.addSource('route-current', {type:'geojson', data:{type:'Feature', geometry:{type:'LineString', coordinates:[]}}});
    map.addLayer({ id:'route-current-line', type:'line', source:'route-current',
      paint:{ 'line-color':'#f0b264', 'line-width':2.6, 'line-opacity':0.95 } });
  }
  if (!map.getSource('contrail')) {
    map.addSource('contrail', {type:'geojson', data:{type:'Feature', geometry:{type:'LineString', coordinates:[]}}});
    map.addLayer({ id:'contrail-line', type:'line', source:'contrail',
      paint:{ 'line-color':'#cfd6d2', 'line-width':1.3, 'line-opacity':0.4, 'line-dasharray':[1,2] } });
  }
}
map.on('style.load', () => { addOverlays(); rebuild(idx, false); });
map.on('load', () => { addOverlays(); fitAll(false); show(0, false); });
window.addEventListener('resize', () => { if (!playing && idx === 0) fitAll(false); });
"""


def render_journey_player(stops: list[dict], title: str, subtitle: str,
                          label_mode: str = "artist", height: int = 560) -> None:
    """In artist mode the subtitle is progressive (computed client-side from
    the playhead); the `subtitle` argument is its initial value / fallback."""
    js = (VENDOR / "maplibre-gl.js").read_text()
    css = (VENDOR / "maplibre-gl.css").read_text()
    config = json.dumps({"label_mode": label_mode})
    data = json.dumps(stops)
    n = len(stops)
    player_css = PLAYER_CSS.replace("__MAP_NARROW_H__", str(max(320, height - 160))) \
                           .replace("__MAP_H__", str(height))
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{css}</style><style>{player_css}</style></head>
<body>
<div id="wrap" tabindex="0" role="application"
     aria-label="Concert journey map. Space plays or pauses; arrow keys step through shows.">
  <div id="map"></div>
  <div id="season"></div>
  <div id="overlay">
    <div id="jtitle">{title}</div>
    <div id="jsub">{subtitle}</div>
    <div id="card"></div>
  </div>
</div>
<div id="controls">
  <div id="cbar">
    <button id="prev" aria-label="Previous show">‹ Prev</button>
    <button id="play" class="primary" aria-label="Play or pause the journey">► Play Journey</button>
    <button id="nextb" aria-label="Next show">Next ›</button>
    <button id="restart" aria-label="Restart the journey">↺ Restart</button>
    <span role="group" aria-label="Playback speed">
      <button data-speed="1" aria-pressed="true">1×</button>
      <button data-speed="2" aria-pressed="false">2×</button>
      <button data-speed="4" aria-pressed="false">4×</button>
    </span>
    <span id="counter">Show 1 of {n}</span>
  </div>
  <input id="scrub" type="range" min="0" max="{max(n - 1, 0)}" value="0" step="1"
         aria-label="Journey timeline scrubber">
  <div id="route-note">{ROUTE_SENTENCE} Press play to travel it — flights, drives, and arrivals in order; the completed path stays visible like a travel diary.</div>
</div>
<script>{js}</script>
<script>const STOPS = {data}; const CONFIG = {config};
{HEADER_JS}
{PLAYER_JS}</script>
</body></html>"""
    st.iframe(html, height=height + 132)
