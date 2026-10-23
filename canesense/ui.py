"""Reusable UI building blocks (HTML fragments + shell) for CaneSense AI."""
from __future__ import annotations
from html import escape
import pandas as pd
import streamlit as st
from . import service, engine
from .config import APP_NAME, CLOUD_ENDPOINT, IMAGES, MODEL_DIR, DESCRIPTOR
from .data import validate_frame
from .theme import icon, RISK_ICON, data_uri

HEADER_IMAGES = {"field": "field_header.jpg", "irrigation": "irrigation_header.jpg"}


def md(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def health_checks() -> list[tuple[str, bool, str]]:
    """Real checks only: nothing here is a fake 'live' indicator."""
    checks = []
    try:
        service.model_bundle()
        checks.append(("ML model loaded", True, "RandomForest ready"))
    except Exception as e:  # pragma: no cover
        checks.append(("ML model loaded", False, str(e)))
    probs = validate_frame(service.baseline()["current"])
    checks.append(("Dataset validation", not probs, "28 plots valid" if not probs else "; ".join(probs)))
    missing = [f for f in ("hero_sugarcane_1500.jpg", "field_header.jpg") if not (IMAGES / f).exists()]
    checks.append(("Local assets", not missing, "all present" if not missing else f"missing {', '.join(missing)}"))
    checks.append(("Model metrics file", (MODEL_DIR / "metrics.json").exists(), "models/metrics.json"))
    return checks


def chip(text: str, kind: str = "neutral", ico: str | None = None, title: str = "") -> str:
    i = icon(ico, 14) if ico else ""
    return f'<span class="cs-chip {kind}" title="{escape(title)}">{i}{escape(text)}</span>'


def shell(title: str, subtitle: str = "") -> None:
    checks = health_checks()
    ok = all(c[1] for c in checks)
    tip = " · ".join(f"{n}: {'OK' if g else 'FAIL'} ({d})" for n, g, d in checks)
    scn = st.session_state.scenario
    if CLOUD_ENDPOINT:
        cloud = chip("Cloud: endpoint set (unchecked)", "info", "cloud", "Use Cloud Lab to run a real check.")
    else:
        cloud = chip("Cloud: not configured", "neutral", "cloud", "Set CANESENSE_CLOUD_URL to enable the optional cloud check in Cloud Lab.")
    md(f"""<div class="cs-top"><div><h1>{escape(title)}</h1><div class="sub">{escape(subtitle)}</div></div>
    <div class="cs-chips">{chip('Demo mode · synthetic data', 'demo', 'info', 'All farms, plots and readings are synthetic. No real farmer data.')}
    {chip('System healthy' if ok else 'System check failed', 'ok' if ok else 'bad', 'check' if ok else 'alert', tip)}
    {chip('Scenario: ' + scn, 'neutral' if scn == 'Normal Conditions' else 'warn', 'activity')}{cloud}</div></div>""")


def band(key: str, text: str) -> None:
    """Slim photographic page header; falls back to nothing if the image is missing."""
    uri = data_uri(HEADER_IMAGES[key])
    if not uri:
        return
    md(f'<div class="cs-band" style="height:84px;background:linear-gradient(90deg,rgba(14,52,36,.88),rgba(14,52,36,.35)),url(\'{uri}\') center/cover;'
       f'display:flex;align-items:center;padding:0 1.4rem;color:#fff;font-weight:600;font-size:.95rem">{escape(text)}</div>')


def section(title: str, right: str = "") -> None:
    md(f'<div class="cs-sec"><h2>{escape(title)}</h2><span>{escape(right)}</span></div>')


def kpi(label: str, value: str, unit: str = "", note: str = "", ico: str = "layers", tone: str = "green",
        trend: str = "", trend_cls: str = "flat") -> str:
    u = f"<small>{escape(unit)}</small>" if unit else ""
    t = f'<div class="trend {trend_cls}">{escape(trend)}</div>' if trend else ""
    return (f'<div class="cs-card cs-kpi tone-{tone}"><div class="lab">{icon(ico, 15)}{escape(label)}</div>'
            f'<div class="val">{escape(value)}{u}</div><div class="note">{escape(note)}</div>{t}</div>')


def badge(level: str) -> str:
    return f'<span class="cs-badge {level}">{RISK_ICON.get(level, "")} {level}</span>'


def empty(title: str, msg: str) -> None:
    md(f'<div class="cs-empty"><b>{escape(title)}</b>{escape(msg)}</div>')


def delta_chip(now: float, base: float, fmt: str = "{:+.0f}", higher_is_bad: bool = True) -> tuple[str, str]:
    d = now - base
    if st.session_state.get("scenario") == "Normal Conditions" and not st.session_state.get("overrides"):
        return "baseline conditions", "flat"
    if abs(d) < 0.5:
        return "same as normal baseline", "flat"
    cls = "up-bad" if (d > 0) == higher_is_bad else "down-good"
    return f"{fmt.format(d)} vs normal baseline", cls


def action_tone(action: str, urgency: str) -> str:
    if action == engine.A_SENSOR:
        return "Review"
    if action == engine.A_MONITOR:
        return "Low" if urgency == "Low" else "Medium"
    if action == engine.A_IRRIGATE:
        return "High"
    return "Medium"


def reco_card(r: pd.Series, compact: bool = False) -> str:
    tone = action_tone(r.action, r.urgency)
    gauge = f"{r.p_high * 100:.0f}%"
    vol = f"{r.volume_m3:,.0f}" if r.volume_m3 else "—"
    dur = f"{r.duration_h:.1f} h" if r.duration_h else "—"
    moist = "no reading" if pd.isna(r.soil_moisture) else f"{r.soil_moisture:.1f}%"
    facts = "".join(f"<li>{escape(f)}</li>" for f in str(r.factors).split(" | ")[: (2 if compact else 4)])
    caveat = ("" if compact else
              '<div class="caveat">Decision support only. Model trained on synthetic data and not validated on real farms; '
              'a farm manager should confirm before operating pumps.</div>')
    return f"""<div class="cs-card cs-reco {tone}"><div class="top"><span class="pid">{escape(r.plot_id)}
      <span style="color:var(--muted);font-weight:500;font-size:.82rem"> · {escape(r.village)} · {r.area_ha} ha</span></span>{badge(r.urgency) if r.action != engine.A_SENSOR else '<span class="cs-badge Review">Sensor review</span>'}</div>
      <div class="act">{escape(r.action)}</div>
      <div class="grid"><div><b>{vol}</b><span>Water m³</span></div><div><b>{dur}</b><span>Duration</span></div><div><b>{gauge}</b><span>P(high)</span></div></div>
      <div class="why">{escape(r.explanation)}</div><ul>{facts}</ul>
      <div class="why"><b>Inputs:</b> moisture {moist}, ET0 {r.et0:.1f} mm/d, air {r.air_temp:.1f} °C, humidity {r.humidity:.0f}%, rain 24h {r.rain_24h:.0f} mm</div>{caveat}</div>"""


def legend() -> None:
    md('<div class="cs-legend"><span><i style="background:#C5392B"></i>▲ High urgency</span><span><i style="background:#D99A16"></i>◆ Medium</span>'
       '<span><i style="background:#4FAE4B"></i>● Low</span><span>✕ Sensor offline</span><span>Marker size = plot area</span><span>Blue band = illustrative canal</span></div>')


def selected_row(df: pd.DataFrame) -> pd.Series | None:
    pid = st.session_state.get("selected_plot")
    if pid and pid in set(df.plot_id):
        return df[df.plot_id == pid].iloc[0]
    return None
