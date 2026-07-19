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

      /* Compact permanent header — no clipping, modest height. */
      .brand-block { padding:.1rem 0 .5rem; }
      .brand-title { font-size:1.55rem; font-weight:850; letter-spacing:.02em; line-height:1.15;
                     color:var(--paper); overflow:visible; }
      .brand-sub { color:var(--amber); font-size:.72rem; letter-spacing:.2em; text-transform:uppercase;
                   font-weight:700; margin-top:.05rem; }
      [data-testid="stPageLink"] a { text-transform:uppercase; letter-spacing:.14em; font-size:.76rem; }
      [data-testid="stPageLink"] a p { font-size:.76rem !important; font-weight:700; }

      /* Section titles (subpages) — bounded size, no clipped descenders. */
      .hero-title { font-size:clamp(1.6rem,3.4vw,2.6rem); line-height:1.12; font-weight:850;
                    margin:.1rem 0 .5rem; overflow:visible; }

      /* Contextual side rail — reads as one unit with the map. */
      .side-panel { border-left:2px solid var(--amber); padding:.25rem 0 .25rem 1rem; }
      .panel-title { font-weight:850; letter-spacing:.08em; text-transform:uppercase; font-size:1.02rem; margin-bottom:.2rem; }
      .panel-sub { color:var(--muted); font-size:.85rem; margin-bottom:.6rem; }
      .stat-line { display:flex; justify-content:space-between; border-bottom:1px dotted var(--line); padding:.28rem 0; font-size:.92rem; }
      .stat-line b { color:var(--paper); }
      .rank-row { display:flex; justify-content:space-between; padding:.22rem 0; font-size:.9rem; }
      .rank-row .n { color:var(--amber); font-weight:700; font-variant-numeric:tabular-nums; }

      /* ------------------------------------------------------------------ */
      /* Ticket system — printed paper artifacts, not UI cards. One         */
      /* renderer, three variants: upcoming_full, past_torn, journey_compact*/
      /* Square corners, fibrous grain, true perforation, stamped status.   */
      /* Decorative fields derive only from real data (archive № = event).  */
      /* Year is the dominant date element: the journey is about time.      */
      /* ------------------------------------------------------------------ */
      .ticket { display:flex; align-items:stretch; margin:.6rem 0; max-width:700px;
                background:
                  repeating-linear-gradient(90deg, rgba(74,58,30,.028) 0 1px, transparent 1px 4px),
                  radial-gradient(ellipse 120% 90% at 78% 8%, rgba(140,112,62,.12), transparent 60%),
                  radial-gradient(ellipse 100% 120% at 0% 100%, rgba(120,95,50,.08), transparent 55%),
                  linear-gradient(168deg, #f1e7d3 0%, #ecdfc6 60%, #e5d6b8 100%);
                color:#1c1710; border-radius:1px; overflow:visible;
                border:1px solid rgba(58,45,22,.5);
                filter:drop-shadow(0 1px 2px rgba(0,0,0,.35)); position:relative; }
      /* faint handling crease */
      .ticket::after { content:""; position:absolute; top:0; bottom:0; left:62%; width:1px;
                background:linear-gradient(180deg, transparent, rgba(74,58,30,.09) 40%, transparent);
                pointer-events:none; }
      .tk-date { flex:0 0 4.6rem; text-align:center; padding:.5rem .3rem;
                 display:flex; flex-direction:column; justify-content:center; }
      .tk-date .d-year { font-size:1.45rem; font-weight:850; line-height:1; letter-spacing:.02em;
                         font-variant-numeric:tabular-nums; }
      .tk-date .d-rule { width:70%; margin:.26rem auto; border-top:1px solid rgba(58,45,22,.4); }
      .tk-date .d-md { font-size:.68rem; letter-spacing:.18em; font-weight:800; color:#5d5138; }
      .tk-body { flex:1 1 auto; padding:.5rem .85rem .45rem; min-width:0; position:relative; }
      .tk-head { font-size:.52rem; letter-spacing:.26em; text-transform:uppercase; color:#9a8c6a; font-weight:700; }
      .tk-title { font-weight:850; font-size:1.02rem; line-height:1.15; text-transform:uppercase;
                  letter-spacing:.01em; margin-top:.05rem; }
      .tk-venue { font-size:.82rem; font-weight:750; color:#33291a; margin-top:.14rem; }
      .tk-city { font-size:.74rem; color:#5d5138; }
      .tk-also { font-size:.68rem; color:#6b5f45; margin-top:.22rem; border-top:1px solid rgba(58,45,22,.25);
                 padding-top:.2rem; letter-spacing:.03em; }
      .tk-also b { font-weight:800; letter-spacing:.1em; color:#8a7c5c; }
      .tk-meta { font-size:.64rem; color:#8a7c5c; margin-top:.2rem; font-weight:800; letter-spacing:.1em; }
      /* stamped, slightly uneven status mark */
      .tk-status { position:absolute; top:.35rem; right:.5rem; color:rgba(163,74,55,.62);
                   border:1.5px solid rgba(163,74,55,.5); border-radius:1px; padding:.05rem .3rem;
                   font-size:.52rem; font-weight:850; letter-spacing:.2em; transform:rotate(-4deg);
                   mask-image:radial-gradient(ellipse 100% 100% at 50% 50%, black 92%, transparent 100%); }
      /* True perforation: punched-dot column with semicircle edge notches. */
      .tk-perf { flex:0 0 6px; position:relative;
                 background-image:radial-gradient(circle, rgba(28,23,16,.5) 1.4px, transparent 1.6px);
                 background-size:6px 8px; background-repeat:repeat-y; background-position:center; }
      .tk-perf::before, .tk-perf::after { content:""; position:absolute; left:50%; transform:translateX(-50%);
                 width:10px; height:10px; border-radius:50%; background:var(--ink); z-index:1; }
      .tk-perf::before { top:-6px; } .tk-perf::after { bottom:-6px; }
      .tk-stub { flex:0 0 4.6rem; display:flex; flex-direction:column;
                 align-items:center; justify-content:center; gap:.3rem; padding:.5rem .35rem; text-align:center;
                 background:rgba(255,255,255,.28); }
      .tk-admit { font-size:.6rem; letter-spacing:.26em; font-weight:850; writing-mode:vertical-rl;
                  text-orientation:mixed; color:#5d5138; }
      .tk-no { font-size:.62rem; letter-spacing:.08em; color:#9a8c6a; font-variant-numeric:tabular-nums; }
      .tk-stamp { border:2px solid #a34a37; color:#a34a37; border-radius:1px; transform:rotate(-7deg);
                  padding:.1rem .4rem; font-size:.58rem; font-weight:850; letter-spacing:.18em;
                  mask-image:radial-gradient(ellipse 100% 100% at 50% 50%, black 90%, transparent 100%); }

      /* Past: stub torn away, handled and faded but readable. */
      .ticket.torn { max-width:640px; opacity:.9; filter:saturate(.8) brightness(.97) sepia(.08)
                       drop-shadow(0 1px 2px rgba(0,0,0,.3));
                     clip-path:polygon(0 0, 97.2% 0, 98.6% 6%, 97.4% 13%, 99% 21%, 97.6% 30%, 98.8% 38%,
                       97.3% 47%, 99% 55%, 97.5% 64%, 98.7% 72%, 97.2% 81%, 98.9% 90%, 97.5% 100%, 0 100%); }
      .ticket.torn::after { left:58%; }

      /* Compact strip ticket for dense chronological lists. */
      .ticket.compact { max-width:100%; margin:.35rem 0; }
      .ticket.compact .tk-date { flex-basis:3.9rem; padding:.32rem .25rem; }
      .ticket.compact .tk-date .d-year { font-size:1.05rem; }
      .ticket.compact .tk-date .d-rule { margin:.15rem auto; }
      .ticket.compact .tk-date .d-md { font-size:.6rem; }
      .ticket.compact .tk-body { padding:.38rem .7rem .34rem; }
      .ticket.compact .tk-title { font-size:.88rem; }
      .ticket.compact .tk-venue { font-size:.76rem; margin-top:.08rem; }
      .ticket.compact .tk-also { margin-top:.14rem; padding-top:.14rem; }

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

      @media (max-width: 900px) {
        .ticket, .ticket.torn { max-width:100%; }
        .jt-yr { display:none; }
      }
    </style>
    """, unsafe_allow_html=True)


def page_header(years: str = "1995–2026") -> None:
    """Compact permanent header: brand left, uppercase nav right."""
    b, n1, n2, n3, n4 = st.columns([3.2, 0.7, 0.85, 0.75, 0.75], vertical_alignment="center")
    with b:
        st.markdown(
            f'<div class="brand-block"><div class="brand-title">THE LONG ENCORE</div>'
            f'<div class="brand-sub">A Personal Concert Atlas · {years}</div></div>',
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
    """One event as a printed box-office ticket.

    Variants: "upcoming_full" (complete unused printed ticket with attached
    stub), "past_torn" (stub torn away, handled, ARCHIVED stamp),
    "journey_compact" (slim strip). The year dominates the date block — the
    journey is about time. Every printed field derives from real event data;
    the archive number is the event id, presented as decoration. No
    seat/section/row/price/gate values are ever manufactured. `meta` is an
    optional data-derived line (e.g. "TIME #12").
    """
    date = row.event_date
    year = f"{date:%Y}" if date is not None else "—"
    md = f"{date:%b} {date:%d}".upper() if date is not None else "—"
    upcoming = bool(getattr(row, "is_upcoming", 0))
    also = also_listed(row.event_title, bill)
    also_html = (f'<div class="tk-also"><b>ALSO LISTED:</b> '
                 f'{" · ".join(esc(b) for b in also)}</div>') if also else ""
    status = "" if upcoming else '<span class="tk-status">ARCHIVED</span>'
    body = (
        f'<div class="tk-date"><div class="d-year">{year}</div>'
        f'<div class="d-rule"></div><div class="d-md">{md}</div></div>'
        f'<div class="tk-body">{status}<div class="tk-head">My Concert Atlas</div>'
        f'<div class="tk-title">{esc(row.event_title)}</div>'
        f'<div class="tk-venue">{esc(row.venue)}</div>'
        f'<div class="tk-city">{esc(place_line(row.city, row.state_region))}</div>'
        + also_html
        + (f'<div class="tk-meta">{esc(meta)}</div>' if meta else "")
        + '</div>'
    )
    archive_no = f"№ {int(row.event_id):06d}"
    if variant == "upcoming_full":
        stub = (
            f'<div class="tk-perf"></div>'
            f'<div class="tk-stub"><span class="tk-admit">ADMIT ONE</span>'
            f'<span class="tk-stamp">UPCOMING</span><span class="tk-no">{archive_no}</span></div>'
        )
        return f'<div class="ticket full">{body}{stub}</div>'
    if variant == "journey_compact":
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
