"""Design tokens and global CSS for the CaneSense AI Streamlit shell."""
from __future__ import annotations
import base64
from functools import lru_cache
from .config import IMAGES

C = dict(forest="#14432F", forest2="#1D5A41", leaf="#4FAE4B", lime="#B7E36A", bg="#F5F3EA", surface="#FFFFFF",
         ink="#1F2A26", muted="#66736C", line="#E2DFD0", amber="#D99A16", red="#C5392B", blue="#4B7CA6",
         green_soft="#E8F4E3", amber_soft="#FBF1D8", red_soft="#F9E3DF", blue_soft="#E3EEF6")
RISK_COLOR = {"High": C["red"], "Medium": C["amber"], "Low": C["leaf"]}
RISK_SOFT = {"High": C["red_soft"], "Medium": C["amber_soft"], "Low": C["green_soft"]}
RISK_ICON = {"High": "▲", "Medium": "◆", "Low": "●"}   # shape + label so colour is never the only cue

ICONS = {
    "droplet": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "wifi": '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "rain": '<line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>',
    "thermo": '<path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "cloud": '<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
}


def icon(name: str, size: int = 18, color: str = "currentColor") -> str:
    return (f'<svg class="cs-i" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


@lru_cache(maxsize=8)
def data_uri(filename: str) -> str:
    p = IMAGES / filename
    if not p.exists():
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def css() -> str:
    hero = data_uri("hero_sugarcane_1500.jpg")
    hero_rule = f"url('{hero}')" if hero else "none"   # graceful fallback: plain forest gradient
    return f"""
<style>
:root {{
  --forest:{C['forest']}; --forest2:{C['forest2']}; --leaf:{C['leaf']}; --lime:{C['lime']}; --bg:{C['bg']};
  --surface:{C['surface']}; --ink:{C['ink']}; --muted:{C['muted']}; --line:{C['line']};
  --amber:{C['amber']}; --red:{C['red']}; --blue:{C['blue']}; --r:12px;
}}
.stApp {{ font-family: Inter, "Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif; }}
.stApp {{ background: var(--bg); color: var(--ink); }}
.stApp, .stApp > div {{ overflow-x: hidden; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu, [data-testid="stStatusWidget"] {{ display:none !important; }}
header[data-testid="stHeader"] {{ background: transparent; height: 2.2rem; }}
.block-container {{ padding: 1.0rem 2rem 3rem; max-width: 1560px; }}
h1,h2,h3,h4 {{ color: var(--ink); letter-spacing: -0.01em; }}
h1 {{ font-size: 1.55rem !important; font-weight: 700 !important; }}
h2 {{ font-size: 1.15rem !important; font-weight: 650 !important; }}
h3 {{ font-size: 1.0rem !important; font-weight: 650 !important; }}
p, li, label, .stMarkdown {{ font-size: 0.92rem; }}
a {{ color: var(--forest2); }}
/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {{ background: var(--forest); border-right: 0; }}
[data-testid="stSidebar"] * {{ color: #E7EFE9; }}
[data-testid="stSidebar"] [data-testid="stLogo"], [data-testid="stSidebar"] img {{ height: 2.6rem; }}
[data-testid="stSidebarNav"] ul {{ padding-top: .4rem; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 9px; margin: 2px 6px; padding: .45rem .7rem; font-weight: 500; }}
[data-testid="stSidebarNavLink"]:hover {{ background: rgba(255,255,255,.08); }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: rgba(183,227,106,.16); box-shadow: inset 3px 0 0 var(--lime); }}
[data-testid="stSidebarNavLink"][aria-current="page"] * {{ color:#fff; font-weight:650; }}
[data-testid="stSidebarNavLink"]:focus-visible {{ outline: 2px solid var(--lime); }}
.cs-side-foot {{ border-top:1px solid rgba(255,255,255,.14); padding:.8rem .4rem 0; margin-top:1rem; font-size:.78rem; color:#B9CCC1; }}
.cs-side-foot b {{ color:#fff; }}
/* ---------- top bar ---------- */
.cs-top {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:.8rem; }}
.cs-top h1 {{ margin:0; padding:0; }}
.cs-top .sub {{ color:var(--muted); font-size:.85rem; margin-top:.1rem; }}
.cs-chips {{ display:flex; gap:.45rem; flex-wrap:wrap; align-items:center; }}
.cs-chip {{ display:inline-flex; align-items:center; gap:.35rem; padding:.28rem .65rem; border-radius:999px; font-size:.75rem; font-weight:600;
           border:1px solid var(--line); background:var(--surface); color:var(--ink); white-space:nowrap; }}
.cs-chip.demo {{ background:{C['amber_soft']}; border-color:#EBD59A; color:#7A5600; }}
.cs-chip.ok {{ background:{C['green_soft']}; border-color:#BFDDB7; color:#1F5E24; }}
.cs-chip.warn {{ background:{C['amber_soft']}; border-color:#EBD59A; color:#7A5600; }}
.cs-chip.bad {{ background:{C['red_soft']}; border-color:#EDB9B1; color:#8E241A; }}
.cs-chip.info {{ background:{C['blue_soft']}; border-color:#BCD3E4; color:#2D5878; }}
.cs-chip.neutral {{ color:var(--muted); }}
.cs-i {{ flex:none; vertical-align:-3px; }}
/* ---------- cards ---------- */
.cs-card {{ background:var(--surface); border:1px solid var(--line); border-radius:var(--r); padding:.95rem 1.05rem; box-shadow:0 1px 2px rgba(20,67,47,.04); }}
.cs-card h4 {{ margin:0 0 .45rem; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-weight:650; }}
.cs-kpi {{ display:flex; flex-direction:column; gap:.1rem; min-height:118px; }}
.cs-kpi .lab {{ display:flex; align-items:center; gap:.4rem; color:var(--muted); font-size:.76rem; font-weight:650; text-transform:uppercase; letter-spacing:.05em; }}
.cs-kpi .val {{ font-size:1.85rem; font-weight:720; line-height:1.15; color:var(--ink); font-variant-numeric: tabular-nums; }}
.cs-kpi .val small {{ font-size:.85rem; font-weight:600; color:var(--muted); margin-left:.2rem; }}
.cs-kpi .note {{ color:var(--muted); font-size:.78rem; }}
.cs-kpi .trend {{ font-size:.76rem; font-weight:650; }}
.cs-kpi .trend.up-bad {{ color:var(--red); }} .cs-kpi .trend.down-good {{ color:#2C7A2F; }} .cs-kpi .trend.flat {{ color:var(--muted); }}
.cs-kpi.tone-red {{ border-top:3px solid var(--red); }} .cs-kpi.tone-amber {{ border-top:3px solid var(--amber); }}
.cs-kpi.tone-green {{ border-top:3px solid var(--leaf); }} .cs-kpi.tone-blue {{ border-top:3px solid var(--blue); }}
.cs-badge {{ display:inline-flex; align-items:center; gap:.25rem; padding:.12rem .55rem; border-radius:999px; font-size:.72rem; font-weight:700; white-space:nowrap; }}
.cs-badge.High {{ background:{C['red_soft']}; color:#8E241A; }} .cs-badge.Medium {{ background:{C['amber_soft']}; color:#7A5600; }}
.cs-badge.Low {{ background:{C['green_soft']}; color:#1F5E24; }} .cs-badge.Review {{ background:{C['blue_soft']}; color:#2D5878; }}
.cs-badge.neutral {{ background:#EEEDE4; color:var(--muted); }}
.cs-sec {{ display:flex; align-items:baseline; justify-content:space-between; margin:1.1rem 0 .5rem; }}
.cs-sec h2 {{ margin:0 !important; padding:0 !important; font-size:1.15rem !important; font-weight:700 !important; }} .cs-sec > span {{ color:var(--muted); font-size:.8rem; }}
.cs-reco {{ border-left:4px solid var(--leaf); animation: csfade .35s ease-out; }}
.cs-reco.High {{ border-left-color:var(--red); }} .cs-reco.Medium {{ border-left-color:var(--amber); }} .cs-reco.Review {{ border-left-color:var(--blue); }}
.cs-reco .top {{ display:flex; justify-content:space-between; align-items:center; gap:.5rem; margin-bottom:.35rem; }}
.cs-reco .pid {{ font-weight:720; font-size:1rem; }} .cs-reco .act {{ font-weight:680; font-size:1.0rem; margin:.1rem 0 .3rem; }}
.cs-reco .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:.5rem; margin:.5rem 0; }}
.cs-reco .grid div {{ background:var(--bg); border-radius:8px; padding:.4rem .55rem; }}
.cs-reco .grid b {{ display:block; font-size:1.05rem; font-variant-numeric:tabular-nums; }} .cs-reco .grid span {{ font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }}
.cs-reco ul {{ margin:.2rem 0 .3rem 1.1rem; padding:0; color:#3C4943; font-size:.84rem; }}
.cs-reco .why {{ color:#3C4943; font-size:.86rem; }} .cs-reco .caveat {{ color:var(--muted); font-size:.76rem; margin-top:.4rem; }}
@keyframes csfade {{ from {{ opacity:.0; transform:translateY(4px); }} to {{ opacity:1; transform:none; }} }}
.cs-empty {{ text-align:center; padding:2.2rem 1rem; color:var(--muted); background:var(--surface); border:1px dashed var(--line); border-radius:var(--r); }}
.cs-empty b {{ display:block; color:var(--ink); font-size:1rem; margin-bottom:.2rem; }}
.cs-legend {{ display:flex; gap:1rem; flex-wrap:wrap; font-size:.78rem; color:var(--muted); margin:.3rem 0; }}
.cs-legend i {{ display:inline-block; width:.7rem; height:.7rem; border-radius:3px; margin-right:.3rem; vertical-align:-1px; }}
.cs-scn {{ min-height:112px; }}
.cs-scn .nm {{ font-weight:700; font-size:.95rem; }} .cs-scn .bl {{ color:var(--muted); font-size:.8rem; margin-top:.15rem; }}
.cs-scn.active {{ border-color:var(--forest2); box-shadow:0 0 0 2px rgba(29,90,65,.18); }}
.cs-scn.preview {{ border-color:var(--leaf); border-style:dashed; }}
.cs-delta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:.6rem; }}
.cs-delta div {{ background:var(--bg); border-radius:10px; padding:.55rem .7rem; }}
.cs-delta span {{ font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; font-weight:650; display:block; }}
.cs-delta b {{ font-size:1.15rem; font-variant-numeric:tabular-nums; }} .cs-delta em {{ font-style:normal; font-size:.78rem; font-weight:700; margin-left:.3rem; }}
.cs-delta em.bad {{ color:var(--red); }} .cs-delta em.good {{ color:#2C7A2F; }} .cs-delta em.same {{ color:var(--muted); }}
/* ---------- hero ---------- */
.st-key-hero {{ position:relative; border-radius:16px; padding:1.6rem 2rem 1.3rem; margin-bottom:.9rem; color:#fff; overflow:hidden;
  background: linear-gradient(95deg, rgba(10,44,30,.93) 0%, rgba(14,52,36,.80) 42%, rgba(14,52,36,.20) 100%), {hero_rule}, var(--forest);
  background-size: cover; background-position: center 38%; }}
.st-key-hero h1, .st-key-hero p, .st-key-hero span {{ color:#fff; }}
.st-key-hero h1 {{ font-size:2.35rem !important; margin:.15rem 0 .35rem; font-weight:760 !important; }}
.st-key-hero .eyebrow {{ color:var(--lime); font-size:.76rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }}
.st-key-hero p.lead {{ max-width:36rem; font-size:1.02rem; color:#E7EFE9; margin-bottom:.9rem; }}
.st-key-hero a[data-testid="stPageLink-NavLink"] {{ border-radius:9px; padding:.5rem 1rem; font-weight:650; border:1px solid rgba(255,255,255,.55); background:rgba(255,255,255,.06); }}
.st-key-hero a[data-testid="stPageLink-NavLink"]:hover {{ background:rgba(255,255,255,.18); }}
.st-key-hero .st-key-cta1 a[data-testid="stPageLink-NavLink"] {{ background:var(--lime); border-color:var(--lime); }}
.st-key-hero .st-key-cta1 a[data-testid="stPageLink-NavLink"] * {{ color:var(--forest) !important; }}
.st-key-hero a:focus-visible {{ outline:3px solid #fff; outline-offset:2px; }}
.st-key-hero .photo-credit {{ position:absolute; right:.9rem; bottom:.4rem; font-size:.66rem; color:rgba(255,255,255,.7); }}
.cs-band {{ border-radius:14px; overflow:hidden; position:relative; margin-bottom:.8rem; }}
/* ---------- widgets ---------- */
.stButton > button, .stDownloadButton > button {{ border-radius:9px; font-weight:620; border:1px solid var(--line); background:var(--surface); color:var(--ink);
   transition: background .15s, box-shadow .15s, transform .05s; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:var(--forest2); color:var(--forest); background:#F8FBF4; }}
.stButton > button:active, .stDownloadButton > button:active {{ transform:translateY(1px); }}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{ outline:3px solid rgba(79,174,75,.55); outline-offset:1px; }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{ background:var(--forest2); border-color:var(--forest2); color:#fff; }}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{ background:var(--forest); color:#fff; }}
.stButton > button:disabled {{ opacity:.5; cursor:not-allowed; }}
[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{ border-radius:9px; }}
[data-testid="stDataFrame"] {{ border:1px solid var(--line); border-radius:var(--r); overflow:hidden; }}
[data-testid="stTabs"] button[role="tab"] {{ font-weight:600; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color:var(--forest); }}
[data-testid="stExpander"] {{ border:1px solid var(--line); border-radius:var(--r); background:var(--surface); }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:var(--r); }}
[data-testid="stMetricValue"] {{ font-size:1.35rem !important; }} [data-testid="stMetricLabel"] {{ font-size:.78rem; color:var(--muted); }}
div[data-testid="stMetric"] {{ background:var(--surface); border:1px solid var(--line); border-radius:var(--r); padding:.6rem .8rem; }}
.js-plotly-plot, .plotly {{ max-width:100%; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; transition:none !important; }} }}
@media (max-width: 1100px) {{
  .block-container {{ padding: .8rem 1rem 2rem; }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap:.7rem; }}
  [data-testid="stColumn"] {{ min-width: calc(50% - .7rem) !important; flex: 1 1 calc(50% - .7rem) !important; }}
  .st-key-hero {{ padding:1.2rem 1.2rem 1rem; }} .st-key-hero h1 {{ font-size:1.9rem !important; }}
}}
@media (max-width: 800px) {{
  .cs-kpi {{ min-height: 0; }} .cs-kpi .val {{ font-size:1.5rem; }}
  [data-testid="stColumn"] {{ min-width: 100% !important; flex-basis:100% !important; }}
  .cs-reco .grid {{ grid-template-columns:repeat(2,1fr); }}
}}
</style>
"""
