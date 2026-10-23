"""Composite Streamlit panels shared by several views (plot detail, filter bar)."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from . import charts, engine, state, ui
from .theme import icon


def recent_events(r: pd.Series, hist: pd.DataFrame) -> list[tuple[str, str]]:
    h = hist[hist.plot_id == r.plot_id].sort_values("date").reset_index(drop=True)
    ev = []
    for i in range(1, len(h)):
        d = h.loc[i]
        rise = d.soil_moisture - h.loc[i - 1, "soil_moisture"]
        if d.rain_24h >= 5:
            ev.append((f"{d.date:%d %b}", f"Rain {d.rain_24h:.0f} mm recorded"))
        elif rise > 5:
            ev.append((f"{d.date:%d %b}", f"Moisture rose {rise:.0f} pts (irrigation event)"))
    if r.soil_moisture == r.soil_moisture and r.soil_moisture < r.stage_threshold:
        ev.append((f"{h.date.max():%d %b}", f"Moisture {r.soil_moisture:.1f}% fell below the {r.stage_threshold}% trigger"))
    if r.sensor_status != "Online":
        ev.append((f"{h.date.max():%d %b}", f"Sensor {r.sensor_status.lower()} - {r.data_quality}"))
    if st.session_state.overrides.get(r.plot_id):
        ev.append(("Now", f"Simulated irrigation of {st.session_state.overrides[r.plot_id]:.0f} mm applied"))
    return ev[-6:][::-1]


def plot_detail(r: pd.Series, hist: pd.DataFrame, key: str = "d") -> None:
    ph = hist[hist.plot_id == r.plot_id]
    ui.md(f'<div class="cs-card"><div style="display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap">'
          f'<div><span style="font-size:1.15rem;font-weight:720">{r.plot_id}</span> <span style="color:var(--muted)">· {r.village} · {r.crop_stage} · {r.variety} · '
          f'{r.soil_type} · {r.irrigation_type} · {r.area_ha} ha</span></div>{ui.badge(r.urgency)}</div></div>')
    mo = "no reading" if pd.isna(r.soil_moisture) else f"{r.soil_moisture:.1f}%"
    cols = st.columns(5)
    for c, (lab, val) in zip(cols, [("Soil moisture", mo), ("Soil temp", f"{r.soil_temp:.1f} °C"), ("Air temp", f"{r.air_temp:.1f} °C"),
                                    ("Humidity", f"{r.humidity:.0f}%"), ("ET0", f"{r.et0:.1f} mm/d")]):
        c.metric(lab, val)
    left, right = st.columns([3, 2])
    with left:
        st.markdown("**Moisture history (21 days)**")
        st.plotly_chart(charts.plot_history(ph, r.stage_threshold), width="stretch", key=f"{key}_hist_{r.plot_id}",
                        config={"displayModeBar": False})
        st.caption(f"Line chart of daily soil moisture for {r.plot_id} against its irrigation trigger of {r.stage_threshold}%.")
    with right:
        st.markdown("**AI prediction**")
        st.plotly_chart(charts.prob_bar(r), width="stretch", key=f"{key}_prob_{r.plot_id}", config={"displayModeBar": False})
        st.caption(f"Predicted urgency: **{r.urgency}** (confidence {r.confidence * 100:.0f}%)" + (" · moisture imputed from village median" if r.imputed else ""))
    a, b = st.columns([3, 2])
    with a:
        st.markdown("**Recommended action**")
        ui.md(ui.reco_card(r))
    with b:
        st.markdown("**Recent events**")
        ev = recent_events(r, hist)
        if ev:
            ui.md("<div class='cs-card'>" + "".join(f"<div style='display:flex;gap:.6rem;padding:.25rem 0;border-bottom:1px solid var(--line);font-size:.84rem'>"
                                                    f"<b style='min-width:3.6rem'>{d}</b><span>{t}</span></div>" for d, t in ev) + "</div>")
        else:
            ui.empty("No notable events", "Nothing unusual in the last 21 days.")
        st.markdown("**Sensor health & data quality**")
        kind = {"OK": "ok", }.get(r.data_quality, "warn" if r.sensor_status == "Degraded" else "bad")
        ui.md(f'<div class="cs-card">{ui.chip(r.sensor_status, kind, "wifi")} {ui.chip("Battery " + str(int(r.battery_pct)) + "%", "ok" if r.battery_pct >= 40 else "warn", "activity")}'
              f'<div style="margin-top:.5rem;font-size:.84rem">{icon("info", 14)} Data quality: <b>{r.data_quality}</b><br>Sensor ID {r.sensor_id}</div></div>')


FILTER_KEYS = dict(q="f_q", risk="f_risk", stage="f_stage", sensor="f_sensor", village="f_village", action="f_action")


def reset_filters() -> None:
    for k in FILTER_KEYS.values():
        st.session_state.pop(k, None)


def apply_filters(df: pd.DataFrame, q="", risk=None, stage=None, sensor=None, village=None, action=None) -> pd.DataFrame:
    out = df
    if q:
        ql = q.strip().lower()
        out = out[out.plot_id.str.lower().str.contains(ql) | out.village.str.lower().str.contains(ql)]
    for col, vals in (("urgency", risk), ("crop_stage", stage), ("sensor_status", sensor), ("village", village), ("action", action)):
        if vals:
            out = out[out[col].isin(vals)]
    return out


def map_chart(df: pd.DataFrame, key: str, tiles: bool = False, height: int | None = None) -> None:
    """Render the farm map; a click on a plot updates the shared `selected_plot` state."""
    fig = charts.field_map(df, st.session_state.get("selected_plot"), tiles)
    if height:
        fig.update_layout(height=height)
    ev = st.plotly_chart(fig, width="stretch", key=key, on_select="rerun", selection_mode="points",
                         config={"displayModeBar": False, "scrollZoom": False})
    pts = ev.selection.points if ev and ev.selection else []
    if pts:
        cd = pts[0].get("customdata")
        pid = cd[0] if cd else None
        if pid and pid != st.session_state.get(key + "_last"):
            st.session_state[key + "_last"] = pid
            state.select_plot(pid)
            st.rerun()
