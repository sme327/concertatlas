"""The journey player: a self-contained client-side map animation.

MapLibre GL JS is vendored locally (assets/vendor) and inlined into the
component, so the player itself works offline; only the Carto basemap tiles
still require an internet connection. All playback state (index, playing,
speed, scrub position, accumulated route, repeat counts, detail card,
progressive header) lives inside the component — Streamlit only supplies the
ordered journey data.

Journey design:
- The route accumulates like a travel diary: earlier segments stay visible at
  ~38% opacity, the current segment is brighter and animated.
- Markers use "concert gravity": near-constant size, color intensity and glow
  scale with how often that location appears in the whole selected journey.
- The header count and year span grow with the playhead — the story is told
  in order, not spoiled by the lifetime total (the quiet "Show N of M"
  counter is the only forward reference).
- The ticket is a physical paper artifact laid over the map, not a UI card.
- When playback completes, the map stays as a summary of the full route.
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
  /* Overlay: bare text + one paper artifact. No containing panel. */
  #overlay { position:absolute; top:12px; left:12px; z-index:5; width:min(330px, 78vw);
             pointer-events:none; }
  #jtitle { color:#eee7da; font-weight:850; font-size:1.05rem; letter-spacing:.06em; text-transform:uppercase;
            text-shadow:0 1px 8px rgba(0,0,0,.85); }
  #jsub { color:#e89a3d; font-size:.7rem; letter-spacing:.18em; text-transform:uppercase; font-weight:800;
          margin-bottom:.55rem; text-shadow:0 1px 6px rgba(0,0,0,.85); font-variant-numeric:tabular-nums; }
  #card { pointer-events:auto; filter:drop-shadow(0 2px 3px rgba(0,0,0,.45)); }

  /* ---- The ticket: printed paper, square corners, true perforation. ---- */
  .jticket { display:flex; position:relative; align-items:stretch;
             background:
               repeating-linear-gradient(90deg, rgba(74,58,30,.028) 0 1px, transparent 1px 4px),
               radial-gradient(ellipse 120% 90% at 78% 8%, rgba(140,112,62,.12), transparent 60%),
               radial-gradient(ellipse 100% 120% at 0% 100%, rgba(120,95,50,.08), transparent 55%),
               linear-gradient(168deg,#f1e7d3 0%, #ecdfc6 60%, #e5d6b8 100%);
             color:#1c1710; border-radius:1px; overflow:visible;
             border:1px solid rgba(58,45,22,.5); }
  /* faint handling crease */
  .jticket::after { content:""; position:absolute; top:0; bottom:0; left:62%; width:1px;
             background:linear-gradient(180deg, transparent, rgba(74,58,30,.09) 40%, transparent);
             pointer-events:none; }
  .jt-stubwrap { flex:0 0 4.2rem; display:flex; align-items:stretch; position:relative; }
  .jt-date { flex:1; text-align:center; padding:.5rem .25rem; display:flex; flex-direction:column;
             justify-content:center; }
  .jt-year { font-size:1.45rem; font-weight:850; line-height:1; font-variant-numeric:tabular-nums;
             letter-spacing:.02em; }
  .jt-rule { width:70%; margin:.28rem auto; border-top:1px solid rgba(58,45,22,.4); }
  .jt-md { font-size:.66rem; letter-spacing:.18em; font-weight:800; color:#5d5138; }
  /* perforation: punched-dot column with semicircle notches top and bottom */
  .jt-perf { flex:0 0 6px; position:relative;
             background-image:radial-gradient(circle, rgba(28,23,16,.5) 1.4px, transparent 1.6px);
             background-size:6px 8px; background-repeat:repeat-y; background-position:center; }
  .jt-perf::before, .jt-perf::after { content:""; position:absolute; left:50%; transform:translateX(-50%);
             width:10px; height:10px; border-radius:50%; background:#0c1012; }
  .jt-perf::before { top:-6px; } .jt-perf::after { bottom:-6px; }
  .jt-main { padding:.5rem .65rem .45rem; min-width:0; flex:1; position:relative; }
  .jt-head { font-size:.52rem; letter-spacing:.26em; text-transform:uppercase; color:#9a8c6a; font-weight:700; }
  .jt-t { font-weight:850; font-size:1rem; text-transform:uppercase; line-height:1.12; letter-spacing:.01em;
          margin-top:.06rem; }
  .jt-venue { font-size:.8rem; font-weight:750; color:#33291a; margin-top:.14rem; }
  .jt-city { font-size:.72rem; color:#5d5138; }
  .jt-also { font-size:.64rem; color:#6b5f45; margin-top:.22rem; border-top:1px solid rgba(58,45,22,.25);
             padding-top:.2rem; letter-spacing:.03em; }
  .jt-also b { font-weight:800; letter-spacing:.1em; color:#8a7c5c; }
  .jt-meta { font-size:.64rem; color:#8a7c5c; margin-top:.2rem; font-weight:800; letter-spacing:.1em; }
  .jt-mile { font-size:.66rem; color:#7c6a48; margin-top:.12rem; font-style:italic; }
  .jt-note { color:#a34a37; font-weight:800; }
  .jt-stamp { position:absolute; top:.35rem; right:.45rem; color:rgba(163,74,55,.62);
              border:1.5px solid rgba(163,74,55,.5); border-radius:1px; padding:.06rem .3rem;
              font-size:.52rem; font-weight:850; letter-spacing:.2em; transform:rotate(-4deg);
              mask-image:radial-gradient(ellipse 100% 100% at 50% 50%, black 92%, transparent 100%); }

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
     MapLibre owns the inline `transform` on .lemarker (the marker root).
     Never animate or overwrite transform on .lemarker itself; all visuals
     (scale, pulse, glow, ring, color) belong to the inner .dot only. */
  .lemarker { position:relative; }
  .lemarker .dot { position:absolute; inset:0; border-radius:50%;
              border:1px solid rgba(238,231,218,.45); }
  .lemarker .cnt { position:absolute; top:-9px; right:-9px; background:#241d12; color:#e89a3d;
              border:1px solid #e89a3d; border-radius:8px; font-size:9px; font-weight:800;
              padding:0 4px; line-height:13px; z-index:1; }
  .lemarker.current .dot { border:2px solid #f7e8c9; }
  @keyframes lepulse { 0%{transform:scale(1)} 50%{transform:scale(1.5)} 100%{transform:scale(1)} }
  .lemarker.current.pulse .dot { animation:lepulse 1.1s ease-in-out infinite; }
  @media (prefers-reduced-motion: reduce) { .lemarker.current.pulse .dot { animation:none; } }

  @media (max-width: 700px) {
    /* Narrow widths: ticket moves below the map instead of covering it. */
    #overlay { position:static; width:auto; padding:.5rem .6rem 0; }
    #jtitle, #jsub { text-shadow:none; }
    #wrap { height:__MAP_NARROW_H__px; }
  }
"""

# Progressive header logic, kept separate so tests can execute it with node.
HEADER_JS = """
function headerCount(n) { return n + (n === 1 ? ' TIME SEEN' : ' TIMES SEEN'); }
function headerSpan(firstYear, currentYear) {
  return firstYear === currentYear ? String(firstYear) : firstYear + '\\u2013' + currentYear;
}
function headerLine(stops, i) {
  // The header reflects the playhead: count of events reached so far and the
  // year span reached so far. Upcoming events count only once reached.
  const y0 = Number(stops[0].event_date.slice(0, 4));
  let yc = y0;
  for (let k = 1; k <= i; k++) yc = Math.max(yc, Number(stops[k].event_date.slice(0, 4)));
  return headerCount(i + 1) + ' \\u00b7 ' + headerSpan(y0, yc);
}
"""

PLAYER_JS = """
const RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const N = STOPS.length;
let idx = 0, playing = false, timer = null, speed = 1, raf = null;

const withCoords = STOPS.filter(s => s.has_coords);
function coordKey(s) { return s.latitude.toFixed(6) + ',' + s.longitude.toFixed(6); }

// --- Concert gravity: total visits per location across the WHOLE journey.
const TOTALS = {};
withCoords.forEach(s => { const k = coordKey(s); TOTALS[k] = (TOTALS[k] || 0) + 1; });
const MAXTOT = Math.max(1, ...Object.values(TOTALS));
function gravity(k) { return Math.sqrt((TOTALS[k] || 1) / MAXTOT); }  // 0..1
function gravityColor(t) {
  const r = Math.round(243 + (198-243)*t), g = Math.round(217 + (86-217)*t), b = Math.round(167 + (16-167)*t);
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}

const map = new maplibregl.Map({
  container: 'map', attributionControl: {compact:true},
  style: { version: 8, sources: { carto: { type:'raster',
      tiles:['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
             'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
             'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
      tileSize:256, attribution:'&copy; OpenStreetMap contributors &copy; CARTO' } },
    layers: [{ id:'base', type:'raster', source:'carto' }] },
  center: [-95, 39], zoom: 3, keyboard: false });
map.addControl(new maplibregl.NavigationControl({showCompass:false}), 'top-right');

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
  if (b) map.fitBounds(b, { padding: boundsPadding(), duration: (animate && !RM) ? 900 : 0, maxZoom: 9 });
}

let markers = {};   // coordKey -> {marker, el, count}

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
function setLine(id, coords) {
  map.getSource(id).setData({type:'Feature', geometry:{type:'LineString', coordinates: coords}});
}

function esc(t) { const d = document.createElement('div'); d.textContent = t ?? ''; return d.innerHTML; }
function ordinal(n) {
  const s = ['th','st','nd','rd'], v = n % 100;
  return n + (s[(v-20)%10] || s[v] || s[0]);
}

function milestone(s) {
  // Exactly one data-derived milestone, most meaningful first; nothing that
  // merely repeats what the ticket already shows.
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
  // The event title already names the act; only genuinely additional names
  // get a labeled secondary line ("ALSO LISTED" — roles are never inferred).
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
      '<div class="jt-year">' + dt.getFullYear() + '</div>' +
      '<div class="jt-rule"></div>' +
      '<div class="jt-md">' + mon + ' ' + String(dt.getDate()).padStart(2,'0') + '</div>' +
    '</div></div>' +
    '<div class="jt-perf"></div>' +
    '<div class="jt-main">' +
      '<span class="jt-stamp">' + status + '</span>' +
      '<div class="jt-head">My Concert Atlas</div>' +
      '<div class="jt-t">' + esc(s.event_title) + '</div>' +
      '<div class="jt-venue">' + esc(s.venue_name) + '</div>' +
      '<div class="jt-city">' + esc(s.city_name) + (s.state_region ? ', ' + esc(s.state_region) : '') + '</div>' +
      (also.length ? '<div class="jt-also"><b>ALSO LISTED:</b> ' + also.map(esc).join(' \\u00b7 ') + '</div>' : '') +
      '<div class="jt-meta">TIME #' + s.appearance_number + '</div>' +
      (mile ? '<div class="jt-mile">' + mile + '</div>' : '') +
      note +
    '</div></div>';
  // Progressive header: count and year span reflect the playhead only.
  if (CONFIG.label_mode === 'artist') {
    document.getElementById('jsub').textContent = headerLine(STOPS, s.appearance_number - 1);
  }
}

function styleMarker(m, key, isCurrent) {
  const t = gravity(key);
  const size = Math.round(12 + 5 * t);           // near-constant size; color carries meaning
  m.el.style.width = size + 'px';                // sizes the MapLibre-positioned root…
  m.el.style.height = size + 'px';
  const dot = m.el.querySelector('.dot');        // …but all visuals live on the inner dot
  dot.style.background = gravityColor(t);
  dot.style.boxShadow = '0 0 ' + (4 + 12*t) + 'px ' + (1 + 3*t) + 'px rgba(232,154,61,' + (0.25 + 0.45*t).toFixed(2) + ')';
  m.el.classList.toggle('current', isCurrent);
  m.el.classList.toggle('pulse', isCurrent && !RM);
}

function rebuild(i, animateSegment) {
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

  const coords = routeCoordsUpTo(i);
  if (raf) { cancelAnimationFrame(raf); raf = null; }
  const past = coords.length >= 2 ? coords.slice(0, -1) : coords;
  setLine('route-past', past.length >= 2 ? past : []);
  if (coords.length >= 2) {
    const a = coords[coords.length-2], b = coords[coords.length-1];
    if (animateSegment && !RM && s.has_coords && s.draw_segment_from_prev) {
      const t0 = performance.now(), dur = 700 / speed;
      function grow(now) {
        const t = Math.min((now - t0) / dur, 1);
        setLine('route-current', [a, [a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t]]);
        if (t < 1) raf = requestAnimationFrame(grow);
      }
      raf = requestAnimationFrame(grow);
    } else {
      setLine('route-current', [a, b]);
    }
  } else {
    setLine('route-current', []);
  }

  renderCard(s);
  document.getElementById('counter').textContent = 'Show ' + (i+1) + ' of ' + N;
  document.getElementById('scrub').value = i;

  if (s.has_coords) {
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
function finishJourney() { pause(); fitAll(true); }
function next() { if (idx < N-1) show(idx+1, true); else finishJourney(); }
function prev() { show(idx-1, false); }

const playBtn = document.getElementById('play');
function tick() { if (idx < N-1) show(idx+1, true); else finishJourney(); }
function play() {
  if (N < 2) return;
  if (idx >= N-1) show(0, false);
  playing = true; playBtn.textContent = '\\u275a\\u275a Pause'; playBtn.classList.remove('primary');
  timer = setInterval(tick, 2400 / speed);
}
function pause() {
  playing = false; playBtn.textContent = '\\u25ba Play Journey'; playBtn.classList.add('primary');
  if (timer) { clearInterval(timer); timer = null; }
}
function toggle() { playing ? pause() : play(); }

document.getElementById('prev').onclick = () => { pause(); prev(); };
document.getElementById('nextb').onclick = () => { pause(); if (idx < N-1) show(idx+1, true); };
playBtn.onclick = toggle;
document.getElementById('restart').onclick = () => { pause(); show(0, false); fitAll(false); };
document.querySelectorAll('[data-speed]').forEach(b => b.onclick = () => {
  speed = Number(b.dataset.speed);
  document.querySelectorAll('[data-speed]').forEach(x => x.setAttribute('aria-pressed', x === b));
  if (playing) { clearInterval(timer); timer = setInterval(tick, 2400 / speed); }
});
const scrub = document.getElementById('scrub');
scrub.oninput = () => { pause(); show(Number(scrub.value), false); };
document.getElementById('wrap').addEventListener('keydown', e => {
  if (e.key === ' ') { e.preventDefault(); toggle(); }
  else if (e.key === 'ArrowRight') { pause(); if (idx < N-1) show(idx+1, true); }
  else if (e.key === 'ArrowLeft') { pause(); prev(); }
  else if (e.key === 'Home') { pause(); show(0, false); }
});

map.on('load', () => {
  map.addSource('route-past', {type:'geojson', data:{type:'Feature', geometry:{type:'LineString', coordinates:[]}}});
  map.addSource('route-current', {type:'geojson', data:{type:'Feature', geometry:{type:'LineString', coordinates:[]}}});
  map.addLayer({ id:'route-past-line', type:'line', source:'route-past',
    paint:{ 'line-color':'#e89a3d', 'line-width':1.8, 'line-opacity':0.38 } });
  map.addLayer({ id:'route-current-line', type:'line', source:'route-current',
    paint:{ 'line-color':'#f0b264', 'line-width':2.6, 'line-opacity':0.95 } });
  fitAll(false);
  show(0, false);
});
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
  <div id="route-note">{ROUTE_SENTENCE} Press play to watch it unfold; the completed path stays visible like a travel diary.</div>
</div>
<script>{js}</script>
<script>const STOPS = {data}; const CONFIG = {config};
{HEADER_JS}
{PLAYER_JS}</script>
</body></html>"""
    st.iframe(html, height=height + 132)
