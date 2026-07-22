from __future__ import annotations

import streamlit as st

from src.formatting import esc, fmt_date_upper, place_line


def inject_css() -> None:
    st.markdown("""
    <style>
      :root {
        --amber:#e89a3d; --amber-dim:rgba(232,154,61,.55); --red:#b4553f;
        --ink:#0c1012; --panel:#111719; --paper:#eee7da; --muted:#a6aaa7; --line:#343a3b;
        --tk-paper:#f2e9d8; --tk-paper-2:#e7dcc4; --tk-ink:#241d12; --tk-line:#a89a7c;
      }
      .stApp { background:var(--ink); color:var(--paper); }
      .block-container { padding-top:1.1rem; padding-bottom:2.5rem; }
      [data-testid="stSidebar"] { background:#111719; border-right:1px solid var(--line); }
      [data-testid="stSidebarNav"] a span { text-transform:uppercase; letter-spacing:.12em; font-size:.78rem; }

      /* Hide only specific Streamlit chrome; keep selectors narrow. */
      [data-testid="stAppDeployButton"] { display:none; }
      [data-testid="stMainMenu"] { display:none; }
      [data-testid="stDecoration"] { display:none; }
      footer { visibility:hidden; }

      h1,h2,h3 { letter-spacing:-0.025em; }
      .eyebrow { color:var(--amber); font-size:.74rem; letter-spacing:.18em; text-transform:uppercase; font-weight:700; }
      .muted { color:var(--muted); }
      .small { font-size:.85rem; }

      /* Single-line header: minimum chrome, maximum content space. */
      .brand-block { padding:.05rem 0 .2rem; }
      .brand-title { font-size:.95rem; font-weight:850; letter-spacing:.14em; line-height:1.2;
                     color:var(--paper); }
      .brand-title .tick { color:var(--amber); }
      .brand-sub { color:var(--amber); font-size:.66rem; letter-spacing:.2em; text-transform:uppercase;
                   font-weight:700; }
      [data-testid="stPageLink"] a { text-transform:uppercase; letter-spacing:.14em; font-size:.76rem; }
      [data-testid="stPageLink"] a p { font-size:.76rem !important; font-weight:700; }

      /* Section titles (subpages) — quiet, museum-label scale. */
      .hero-title { font-size:clamp(1.25rem,2.6vw,1.8rem); line-height:1.1; font-weight:850;
                    margin:.05rem 0 .4rem; overflow:visible; }

      /* Upcoming: responsive grid of ticket cards — every show visible. */
      .ticket-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(290px, 1fr));
                     gap:.7rem; align-items:start; }
      .ticket-grid .ticket { margin:0; max-width:100%; }

      /* Contextual side rail — reads as one unit with the map. */
      .side-panel { border-left:2px solid var(--amber); padding:.25rem 0 .25rem 1rem; }
      .panel-title { font-weight:850; letter-spacing:.08em; text-transform:uppercase; font-size:1.02rem; margin-bottom:.2rem; }
      .panel-sub { color:var(--muted); font-size:.85rem; margin-bottom:.6rem; }
      .stat-line { display:flex; justify-content:space-between; border-bottom:1px dotted var(--line); padding:.28rem 0; font-size:.92rem; }
      .stat-line b { color:var(--paper); }
      .rank-row { display:flex; justify-content:space-between; padding:.22rem 0; font-size:.9rem; }
      .rank-row .n { color:var(--amber); font-weight:700; font-variant-numeric:tabular-nums; }

      /* ------------------------------------------------------------------ */
      /* Ticket system — Grandstand Stub direction (approved design III).   */
      /* Aged manila stock, foxing, faint sunburst, navy + faded-red inks,  */
      /* wood-type capitals, KEEP THIS COUPON stub, ADMIT ONE tape edge.    */
      /* One renderer, three variants: upcoming_full, past_torn,            */
      /* journey_compact. Decorative fields derive only from real data      */
      /* (archive № = event id). Year stays the dominant date element.      */
      /* ------------------------------------------------------------------ */
      .ticket { display:flex; align-items:stretch; margin:.65rem 0; max-width:640px;
                color:#23304d; position:relative; border-radius:1px;
                font-family:'Avenir Next Condensed','Futura-CondensedMedium','Arial Narrow','Helvetica Neue',sans-serif;
                background:
                  radial-gradient(circle 2px at 12% 30%, rgba(140,100,50,.18) 40%, transparent 60%),
                  radial-gradient(circle 1.6px at 78% 68%, rgba(140,100,50,.16) 40%, transparent 60%),
                  radial-gradient(circle 2.4px at 55% 12%, rgba(140,100,50,.12) 40%, transparent 60%),
                  repeating-conic-gradient(from 0deg at 50% 46%, rgba(163,56,40,.04) 0 5deg, transparent 5deg 10deg),
                  linear-gradient(160deg,#ead9ab,#dcc88e);
                border:2px solid #23304d;
                box-shadow:inset 0 0 0 3px #ead9ab, inset 0 0 0 5px rgba(35,48,77,.7),
                  0 2px 6px rgba(0,0,0,.4); }
      .tk-stub { flex:0 0 4.4rem; border-right:2px dashed rgba(35,48,77,.75); display:flex;
                 flex-direction:column; align-items:center; justify-content:center; gap:.5rem;
                 padding:.7rem .3rem; background:rgba(255,250,232,.35); }
      .tk-keep { writing-mode:vertical-rl; text-orientation:mixed; font-weight:700; font-size:.6rem;
                 letter-spacing:.26em; }
      .tk-no { font-family:'American Typewriter','Courier New',serif; font-size:.6rem; color:#5a4a2c;
               font-variant-numeric:tabular-nums; }
      .tk-perf { flex:0 0 6px;
                 background-image:radial-gradient(circle, rgba(35,48,77,.45) 1.4px, transparent 1.6px);
                 background-size:6px 8px; background-repeat:repeat-y; background-position:center; }
      .tk-body { flex:1 1 auto; text-align:center; padding:.8rem .9rem 1.15rem; min-width:0;
                 position:relative; }
      .tk-head { font-weight:700; font-size:.6rem; letter-spacing:.3em; color:#a03828; }
      .tk-title { font-weight:800; font-size:1.5rem; line-height:.98; text-transform:uppercase;
                  letter-spacing:.01em; margin-top:.22rem; }
      .tk-at { font-family:'Snell Roundhand','Brush Script MT',cursive; font-size:1rem;
               color:#a03828; margin-top:.12rem; }
      .tk-venue { font-weight:700; font-size:.98rem; text-transform:uppercase; letter-spacing:.1em; }
      .tk-city { font-family:'American Typewriter','Courier New',serif; font-size:.66rem;
                 margin-top:.16rem; color:#5a4a2c; }
      .tk-also { font-family:'American Typewriter','Courier New',serif; font-size:.63rem;
                 color:#5a4a2c; margin-top:.4rem; }
      .tk-also b { font-weight:700; letter-spacing:.08em; color:#a03828; }
      .tk-date { display:flex; justify-content:center; align-items:center; gap:.6rem; margin-top:.5rem; }
      .tk-date .d-year { font-weight:800; font-size:1.5rem; line-height:1.1; border:2px solid #23304d;
                 padding:.04rem .45rem; background:rgba(255,250,232,.5);
                 font-variant-numeric:tabular-nums; }
      .tk-date .d-md { font-weight:700; font-size:.7rem; letter-spacing:.2em; text-align:left;
                 line-height:1.3; }
      .tk-meta { font-weight:700; font-size:.6rem; letter-spacing:.22em; color:#a03828; margin-top:.42rem; }
      .tk-tape { position:absolute; left:0; right:0; bottom:0; font-weight:700; font-size:.5rem;
                 letter-spacing:.4em; color:rgba(35,48,77,.5); white-space:nowrap; overflow:hidden;
                 border-top:1px solid rgba(35,48,77,.35); padding:.14rem 0 .1rem; }
      .tk-seal { position:absolute; top:.5rem; right:.6rem; width:46px; height:46px; border-radius:50%;
                 border:2px solid rgba(160,56,40,.6); color:rgba(160,56,40,.8); display:flex;
                 align-items:center; justify-content:center; font-weight:800; font-size:.5rem;
                 letter-spacing:.12em; transform:rotate(10deg); text-align:center; line-height:1.2;
                 background:radial-gradient(circle, rgba(160,56,40,.07), transparent 70%); }
      .tk-status { position:absolute; top:.5rem; right:.6rem; color:rgba(160,56,40,.65);
                 border:1.5px solid rgba(160,56,40,.5); border-radius:1px; padding:.08rem .34rem;
                 font-size:.54rem; font-weight:800; letter-spacing:.2em; transform:rotate(-4deg); }

      /* Past: coupon torn off the left edge; handled, sepia, still legible. */
      .ticket.torn { max-width:600px; filter:sepia(.18) saturate(.9) brightness(.96);
                     clip-path:polygon(2.6% 0,100% 0,100% 100%,3% 100%,1.4% 91%,3.2% 81%,1.2% 70%,
                       3% 60%,1.5% 49%,3.3% 38%,1.3% 27%,3.1% 16%,1.6% 7%); }

      /* Compact strip for dense chronological lists and drawers. */
      .ticket.compact { max-width:100%; margin:.35rem 0; box-shadow:inset 0 0 0 2px #ead9ab,
                 inset 0 0 0 3px rgba(35,48,77,.6), 0 1px 4px rgba(0,0,0,.35); border-width:1px; }
      .ticket.compact .tk-body { padding:.5rem .7rem .55rem; }
      .ticket.compact .tk-title { font-size:1.05rem; }
      .ticket.compact .tk-at { display:none; }
      .ticket.compact .tk-venue { font-size:.8rem; margin-top:.08rem; }
      .ticket.compact .tk-date { margin-top:.3rem; }
      .ticket.compact .tk-date .d-year { font-size:1.05rem; border-width:1.5px; }
      .ticket.compact .tk-also { margin-top:.25rem; }

      /* Journey timeline strip beneath the standard map. */
      .jt-strip { display:flex; align-items:flex-end; gap:2px; margin:.7rem 0 .2rem; height:52px; }
      .jt-col { flex:1 1 auto; display:flex; flex-direction:column; align-items:center; gap:3px; min-width:0; }
      .jt-bar { width:100%; max-width:22px; background:var(--amber-dim); border-radius:2px 2px 0 0; }
      .jt-col.hot .jt-bar { background:var(--amber); }
      .jt-yr { color:var(--muted); font-size:.58rem; font-variant-numeric:tabular-nums; letter-spacing:.02em; }

      /* Artist constellation rows */
      .const-row { display:flex; align-items:baseline; gap:.7rem; padding:.32rem 0; border-bottom:1px dotted var(--line); }
      .const-name { flex:1 1 auto; font-weight:650; }
      .const-name.w2 { font-weight:750; font-size:1.04rem; }
      .const-name.w3 { font-weight:850; font-size:1.12rem; }
      .const-count { color:var(--amber); font-size:.8rem; letter-spacing:.06em; white-space:nowrap; }
      .const-years { color:var(--muted); font-size:.76rem; white-space:nowrap; font-variant-numeric:tabular-nums; }
      .const-years .dot { color:var(--amber-dim); }

      /* Year history strip */
      .strip { display:flex; align-items:center; gap:.35rem; margin:.5rem 0 .2rem; flex-wrap:wrap; }
      .strip .yr { color:var(--muted); font-size:.75rem; font-variant-numeric:tabular-nums; }
      .strip .seg { height:2px; background:var(--line); flex:1 1 6px; min-width:6px; }
      .strip .node { width:9px; height:9px; border-radius:50%; background:var(--amber); flex:0 0 auto; }

      .big-number { font-size:2rem; font-weight:800; color:var(--paper); line-height:1.05; }

      .mini-card { border:1px solid var(--line); border-left:3px solid var(--amber); border-radius:4px;
                   padding:.7rem .85rem; margin-bottom:.6rem; }
      .mini-card .k { color:var(--amber); font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; font-weight:800; }

      .bar-row { display:flex; align-items:center; gap:.6rem; padding:.18rem 0; font-size:.86rem; }
      .bar-label { flex:0 0 42%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .bar-track { flex:1 1 auto; height:8px; background:#1a2124; border-radius:4px; }
      .bar-fill { height:8px; background:var(--amber-dim); border-radius:4px; }
      .bar-val { flex:0 0 2.2rem; text-align:right; color:var(--muted); font-variant-numeric:tabular-nums; }

      .event-date { color:var(--amber); font-weight:800; letter-spacing:.1em; font-size:.78rem; }
      .event-title { font-weight:750; font-size:1.02rem; }
      .event-bill { color:var(--muted); font-size:.88rem; }

      /* Artist browser — a browsable chip grid, not a developer-style dropdown. */
      [class*="st-key-artist_browser"] input {
        background:#161d21; border:1px solid var(--line); color:var(--paper);
      }
      [class*="st-key-artist_browser"] [data-testid="stButton"] button {
        white-space:pre-line; line-height:1.25; text-align:left; font-size:.82rem;
        padding:.55rem .65rem; border-radius:2px; border:1px solid var(--line);
        background:#161d21; color:var(--paper); min-height:3.4rem;
      }
      [class*="st-key-artist_browser"] [data-testid="stButton"] button p { font-size:.82rem; }
      [class*="st-key-artist_browser"] [data-testid="stButton"] button:hover {
        border-color:var(--amber); color:var(--amber);
      }
      [class*="st-key-artist_browser"] [data-testid="stButton"] button[kind="primary"] {
        background:var(--amber); border-color:var(--amber); color:var(--ink); font-weight:700;
      }

      @media (max-width: 900px) {
        .ticket, .ticket.torn { max-width:100%; }
        .jt-yr { display:none; }
      }
    </style>
    """, unsafe_allow_html=True)


def page_header(years: str = "") -> None:
    """One slim line: brand left, uppercase nav right. No subtitle block."""
    b, n1, n2, n3, n4 = st.columns([3.2, 0.7, 0.85, 0.75, 0.75], vertical_alignment="center")
    with b:
        st.markdown(
            '<div class="brand-block"><div class="brand-title">'
            '<span class="tick">MY</span> CONCERT ATLAS</div></div>',
            unsafe_allow_html=True,
        )
    links = [(n1, "app.py", "ATLAS"), (n2, "pages/1_Artists.py", "ARTISTS"),
             (n3, "pages/2_Shows.py", "SHOWS"), (n4, "pages/3_About_the_Data.py", "ABOUT")]
    for col, target, label in links:
        with col:
            try:
                st.page_link(target, label=label)
            except Exception:
                # Outside a full multipage runtime (e.g. test harness) the page
                # registry is unavailable; the sidebar nav still works there.
                st.markdown(f'<span class="brand-sub">{label}</span>', unsafe_allow_html=True)


def metric(label, value, detail: str = "") -> None:
    st.markdown(
        f'<div><div class="eyebrow">{esc(label)}</div><div class="big-number">{esc(value)}</div>'
        f'<div class="muted small">{esc(detail)}</div></div>',
        unsafe_allow_html=True,
    )


def also_listed(event_title, bill: list[str]) -> list[str]:
    """Names on the bill beyond the event title itself. The ticket shows the
    title once; genuinely additional names get an ALSO LISTED line (the
    source never proves opener/headliner roles, so no roles are implied)."""
    title = str(event_title or "").strip().lower()
    return [b for b in bill if b.strip().lower() != title]


def ticket_html(row, bill: list[str], variant: str = "past_torn", meta: str = "") -> str:
    """One event as a grandstand-style printed ticket (approved direction III).

    Variants: "upcoming_full" (complete ticket with attached KEEP THIS COUPON
    stub and UPCOMING seal), "past_torn" (coupon torn off the left edge,
    sepia-handled, ARCHIVED stamp), "journey_compact" (slim strip). The boxed
    year dominates the date block — the journey is about time. Every printed
    field derives from real event data; the archive number is the event id,
    presented as decoration. No seat/section/row/price/gate values are ever
    manufactured. `meta` is an optional data-derived line (e.g. "TIME #12").
    """
    date = row.event_date
    year = f"{date:%Y}" if date is not None else "—"
    md = f"{date:%b}<br>{date:%d}".upper() if date is not None else "—"
    upcoming = bool(getattr(row, "is_upcoming", 0))
    compact = variant == "journey_compact"
    also = also_listed(row.event_title, bill)
    also_html = (f'<div class="tk-also"><b>ALSO LISTED:</b> '
                 f'{" · ".join(esc(b) for b in also)}</div>') if also else ""
    if variant == "upcoming_full":
        mark = '<span class="tk-seal" role="img" aria-label="UPCOMING">UP<br>COMING</span>'
    elif upcoming:
        mark = '<span class="tk-status">UPCOMING</span>'
    else:
        mark = '<span class="tk-status">ARCHIVED</span>'
    tape = ('<div class="tk-tape">' + " · ".join(["ADMIT ONE"] * 8) + '</div>') if not compact else ""
    body = (
        f'<div class="tk-body">{mark}'
        f'<div class="tk-head">MY CONCERT ATLAS PRESENTS</div>'
        f'<div class="tk-title">{esc(row.event_title)}</div>'
        f'<div class="tk-at">at</div>'
        f'<div class="tk-venue">{esc(row.venue)}</div>'
        f'<div class="tk-city">{esc(place_line(row.city, row.state_region))}</div>'
        + also_html
        + f'<div class="tk-date"><span class="d-year">{year}</span><span class="d-md">{md}</span></div>'
        + (f'<div class="tk-meta">{esc(meta)}</div>' if meta else "")
        + tape
        + '</div>'
    )
    archive_no = f"№ {int(row.event_id):06d}"
    if variant == "upcoming_full":
        stub = (
            f'<div class="tk-stub"><span class="tk-keep">KEEP THIS COUPON</span>'
            f'<span class="tk-no">{archive_no}</span></div>'
            f'<div class="tk-perf"></div>'
        )
        return f'<div class="ticket full">{stub}{body}</div>'
    if compact:
        cls = "ticket compact full" if upcoming else "ticket compact torn"
        return f'<div class="{cls}">{body}</div>'
    return f'<div class="ticket torn">{body}</div>'


def bar_rows_html(frame, label_col: str, value_col: str, limit: int = 10) -> str:
    """Compact horizontal-bar list used for the analytical cuts."""
    rows = frame.head(limit)
    if not len(rows):
        return '<div class="muted small">Nothing in this filter.</div>'
    peak = max(int(rows[value_col].max()), 1)
    out = []
    for _, r in rows.iterrows():
        width = max(int(round(int(r[value_col]) / peak * 100)), 3)
        out.append(
            f'<div class="bar-row"><div class="bar-label">{esc(r[label_col])}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>'
            f'<div class="bar-val">{int(r[value_col])}</div></div>'
        )
    return "".join(out)


def year_strip_html(first_year: int, latest_year: int, active_years: set[int]) -> str:
    """A thin timeline from first to latest visit with a node per active year."""
    if latest_year < first_year:
        first_year, latest_year = latest_year, first_year
    parts = [f'<div class="strip"><span class="yr">{first_year}</span>']
    for year in range(first_year, latest_year + 1):
        if year in active_years:
            parts.append('<span class="node"></span>')
        else:
            parts.append('<span class="seg"></span>')
    parts.append(f'<span class="yr">{latest_year}</span></div>')
    return "".join(parts)


def journey_timeline_html(year_show_counts, highlight_year: int | None = None) -> str:
    """Full-width chronological strip: one column per year, bar height = shows."""
    if not len(year_show_counts):
        return ""
    counts = dict(zip(year_show_counts.year.astype(int), year_show_counts.shows.astype(int)))
    lo, hi = min(counts), max(counts)
    peak = max(counts.values())
    cols = []
    for y in range(lo, hi + 1):
        n = counts.get(y, 0)
        h = max(int(round(n / peak * 44)), 2 if n else 1)
        hot = " hot" if (highlight_year == y or (highlight_year is None and n == peak)) else ""
        label = f'<span class="jt-yr">{str(y)[2:] if y % 5 else y}</span>' if (y % 5 == 0 or y in (lo, hi)) else '<span class="jt-yr">&nbsp;</span>'
        cols.append(f'<div class="jt-col{hot}" title="{y}: {n} shows">'
                    f'<div class="jt-bar" style="height:{h}px"></div>{label}</div>')
    return f'<div class="jt-strip">{"".join(cols)}</div>'


def constellation_html(constellation, limit: int = 14) -> str:
    """Artists at a venue as a weighted visual list with year dots."""
    rows = constellation.head(limit)
    if not len(rows):
        return '<div class="muted small">No artists in this filter.</div>'
    peak = max(int(rows.appearances.max()), 1)
    out = []
    for _, r in rows.iterrows():
        weight = "w3" if r.appearances >= max(3, peak * 0.75) else ("w2" if r.appearances >= 2 else "")
        years = list(r.years)[:6]
        dots = " ".join(f'<span class="dot">●</span> {y}' for y in years)
        if len(list(r.years)) > 6:
            dots += " …"
        out.append(
            f'<div class="const-row"><span class="const-name {weight}">{esc(r.display_name)}</span>'
            f'<span class="const-count">{int(r.appearances)}×</span>'
            f'<span class="const-years">{dots}</span></div>'
        )
    return "".join(out)
