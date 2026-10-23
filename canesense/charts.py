"""Plotly figures with a consistent CaneSense look. Offline-safe (no tiles unless explicitly requested)."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .data import VILLAGES
from .theme import C, RISK_COLOR

FONT = dict(family="Inter, Segoe UI, system-ui, sans-serif", size=12, color=C["ink"])
SYMBOL = {"High": "triangle-up", "Medium": "diamond", "Low": "circle"}


def style(fig: go.Figure, h: int = 300, legend: bool = True) -> go.Figure:
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=28, b=8), font=FONT, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=11)),
                      hoverlabel=dict(bgcolor="#fff", font_size=12, bordercolor=C["line"]))
    fig.update_xaxes(gridcolor="#EDEBDD", zeroline=False, linecolor=C["line"])
    fig.update_yaxes(gridcolor="#EDEBDD", zeroline=False, linecolor=C["line"])
    return fig


def moisture_trend(hist: pd.DataFrame, cur: pd.DataFrame) -> go.Figure:
    h = hist.merge(cur[["plot_id", "urgency", "stage_threshold"]], on="plot_id")
    h["soil_moisture"] = h.soil_moisture.astype(float)
    est = h.groupby("date").agg(m=("soil_moisture", "mean"), thr=("stage_threshold", "mean")).reset_index()
    hi = h[h.urgency == "High"].groupby("date").soil_moisture.mean().reset_index()
    lo = h[h.urgency != "High"].groupby("date").soil_moisture.mean().reset_index()
    f = go.Figure()
    f.add_scatter(x=est.date, y=est.thr, name="Mean irrigation trigger", line=dict(color=C["muted"], dash="dash", width=1.5), hovertemplate="%{y:.1f}%")
    f.add_scatter(x=lo.date, y=lo.soil_moisture, name="Other plots", line=dict(color=C["leaf"], width=2.5), hovertemplate="%{y:.1f}%")
    if len(hi):
        f.add_scatter(x=hi.date, y=hi.soil_moisture, name="High-urgency plots", line=dict(color=C["red"], width=2.5), hovertemplate="%{y:.1f}%")
    f.update_yaxes(title="Soil moisture (% VWC)")
    f.update_layout(hovermode="x unified")
    return style(f, 280)


def urgency_by_village(cur: pd.DataFrame) -> go.Figure:
    t = cur.groupby(["village", "urgency"]).size().unstack(fill_value=0).reindex(columns=["High", "Medium", "Low"], fill_value=0)
    f = go.Figure()
    lab = {"High": "▲ High", "Medium": "◆ Medium", "Low": "● Low"}
    for k in t.columns:
        f.add_bar(y=t.index, x=t[k], name=lab[k], orientation="h", marker_color=RISK_COLOR[k], text=t[k].replace(0, ""), textposition="inside",
                  hovertemplate="%{y}: %{x} plot(s)<extra>" + k + "</extra>")
    f.update_layout(barmode="stack")
    f.update_xaxes(title="Plots", dtick=1)
    f.update_yaxes(autorange="reversed")
    return style(f, 280)


def rainfall_panel(hist: pd.DataFrame, cur: pd.DataFrame) -> go.Figure:
    r = hist.groupby("date").rain_24h.mean().reset_index()
    fc = float(cur.forecast_rain_48h.mean())
    f = go.Figure()
    f.add_bar(x=r.date, y=r.rain_24h, name="Observed (estate mean)", marker_color=C["blue"], hovertemplate="%{y:.1f} mm")
    nxt = r.date.max() + pd.Timedelta(days=1)
    f.add_bar(x=[nxt], y=[fc], name="Forecast 48 h (mean)", marker_color="#A9C6DD", marker_pattern_shape="/", hovertemplate="%{y:.1f} mm forecast")
    f.update_yaxes(title="Rain (mm)")
    return style(f, 200)


def field_map(cur: pd.DataFrame, selected: str | None, tiles: bool = False) -> go.Figure:
    f = go.Figure()
    if tiles:
        for lvl in ["Low", "Medium", "High"]:
            d = cur[cur.urgency == lvl]
            f.add_trace(go.Scattermap(lat=d.lat, lon=d.lon, mode="markers+text", name=lvl, text=d.plot_id.str[-3:],
                        marker=dict(size=d.area_ha * 6 + 10, color=RISK_COLOR[lvl], opacity=.9), customdata=_hover(d),
                        hovertemplate=_HT, textposition="top center", textfont=dict(size=10)))
        f.update_layout(map=dict(style="open-street-map", center=dict(lat=cur.lat.mean(), lon=cur.lon.mean()), zoom=11.3))
        return style(f, 520)
    # offline "field-zone" view: village zones, an illustrative canal, and plot markers
    for v, (lat0, lon0, soil) in VILLAGES.items():
        f.add_shape(type="rect", x0=lon0 - 0.0245, x1=lon0 + 0.0245, y0=lat0 - 0.0115, y1=lat0 + 0.0158, line=dict(color="#D9D5C0", width=1),
                    fillcolor="rgba(205,222,190,.35)", layer="below")
        f.add_annotation(x=lon0 - 0.0238, y=lat0 + 0.0154, text=f"<b>{v}</b>", showarrow=False, xanchor="left", yanchor="top",
                         font=dict(size=11, color=C["forest2"]))
    cx = np.linspace(cur.lon.min() - 0.012, cur.lon.max() + 0.012, 60)
    f.add_scatter(x=cx, y=16.8305 + 0.0022 * np.sin(cx * 420), mode="lines", line=dict(color="#9CC3DE", width=6), hoverinfo="skip",
                  name="Main canal (illustrative)")
    for lvl in ["Low", "Medium", "High"]:
        d = cur[cur.urgency == lvl]
        if d.empty:
            continue
        f.add_scatter(x=d.lon, y=d.lat, mode="markers+text", name={"High": "▲ High", "Medium": "◆ Medium", "Low": "● Low"}[lvl], text=d.plot_id.str[-3:],
                      textposition="bottom center", textfont=dict(size=9, color=C["muted"]), customdata=_hover(d), hovertemplate=_HT,
                      marker=dict(size=(d.area_ha * 4 + 12), color=RISK_COLOR[lvl], symbol=SYMBOL[lvl], line=dict(color="#fff", width=1.5), opacity=.95))
    off = cur[cur.sensor_status == "Offline"]
    if len(off):
        f.add_scatter(x=off.lon, y=off.lat, mode="markers", name="✕ Sensor offline", hoverinfo="skip",
                      marker=dict(symbol="x", size=11, color="#1F2A26", line=dict(width=2)))
    if selected and selected in set(cur.plot_id):
        s = cur[cur.plot_id == selected]
        f.add_scatter(x=s.lon, y=s.lat, mode="markers", name="Selected", hoverinfo="skip",
                      marker=dict(size=s.area_ha * 4 + 26, symbol="circle-open", color=C["forest"], line=dict(width=3)))
    f.update_xaxes(visible=False, range=[cur.lon.min() - 0.012, cur.lon.max() + 0.012])
    f.update_yaxes(visible=False, range=[cur.lat.min() - 0.009, cur.lat.max() + 0.009])
    f.update_layout(clickmode="event+select", dragmode="pan", showlegend=False)
    return style(f, 480).update_layout(showlegend=False)


_HT = ("<b>%{customdata[0]}</b> · %{customdata[1]}<br>Moisture: %{customdata[2]}<br>Urgency: %{customdata[3]}<br>"
       "Action: %{customdata[4]}<extra></extra>")


def _hover(d: pd.DataFrame):
    m = d.soil_moisture.map(lambda v: "no reading" if pd.isna(v) else f"{v:.1f}%")
    return np.stack([d.plot_id, d.village, m, d.urgency, d.action], axis=-1)


def plot_history(h: pd.DataFrame, threshold: float, title: str = "") -> go.Figure:
    h = h.sort_values("date")
    f = go.Figure()
    f.add_scatter(x=h.date, y=h.soil_moisture, mode="lines+markers", name="Soil moisture", line=dict(color=C["forest2"], width=2.5), marker=dict(size=5))
    f.add_hline(y=threshold, line=dict(color=C["red"], dash="dash", width=1.5), annotation_text=f"Trigger {threshold:.0f}%", annotation_position="bottom right")
    jumps = h[h.soil_moisture.diff() > 5]
    if len(jumps):
        f.add_scatter(x=jumps.date, y=jumps.soil_moisture, mode="markers", name="Moisture rise (irrigation/rain)",
                      marker=dict(symbol="triangle-up", size=11, color=C["blue"]))
    f.update_yaxes(title="Moisture (% VWC)")
    f.update_layout(legend=dict(orientation="h", y=-0.32, x=0))
    return style(f, 260).update_layout(legend=dict(orientation="h", y=-0.32, x=0))


def prob_bar(r: pd.Series) -> go.Figure:
    f = go.Figure(go.Bar(x=[r.p_low * 100, r.p_medium * 100, r.p_high * 100], y=["Low", "Medium", "High"], orientation="h",
                         marker_color=[RISK_COLOR["Low"], RISK_COLOR["Medium"], RISK_COLOR["High"]],
                         text=[f"{v * 100:.0f}%" for v in (r.p_low, r.p_medium, r.p_high)], textposition="outside"))
    f.update_xaxes(range=[0, 115], title="Model probability (%)")
    return style(f, 160, legend=False)


def confusion(cm, classes) -> go.Figure:
    f = go.Figure(go.Heatmap(z=cm, x=classes, y=classes, colorscale=[[0, "#F5F3EA"], [1, C["forest2"]]], text=cm, texttemplate="%{text}",
                             showscale=False, hovertemplate="True %{y} → predicted %{x}: %{z}<extra></extra>"))
    f.update_xaxes(title="Predicted")
    f.update_yaxes(title="True", autorange="reversed")
    return style(f, 280, legend=False)


def importance(imp: dict) -> go.Figure:
    k = list(imp)[::-1]
    f = go.Figure(go.Bar(x=[imp[i] for i in k], y=k, orientation="h", marker_color=C["forest2"], hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
    f.update_xaxes(title="Relative importance")
    return style(f, 300, legend=False)


def before_after(before: dict, after: dict) -> go.Figure:
    f = go.Figure()
    labs = ["High", "Medium", "Low"]
    keys = ["high_risk", "medium_risk", "low_risk"]
    f.add_bar(x=labs, y=[before[k] for k in keys], name="Before", marker_color="#BFC8C2", text=[before[k] for k in keys], textposition="outside")
    f.add_bar(x=labs, y=[after[k] for k in keys], name="After", marker_color=[RISK_COLOR[l] for l in labs], text=[after[k] for k in keys], textposition="outside")
    f.update_layout(barmode="group")
    f.update_yaxes(title="Plots")
    return style(f, 250)


def schedule(df: pd.DataFrame) -> go.Figure:
    f = go.Figure()
    for pump, d in df.groupby("pump"):
        for _, r in d.iterrows():
            f.add_trace(go.Bar(y=[pump], x=[(r.end - r.start).total_seconds() * 1000], base=[r.start], orientation="h", name=r.plot_id,
                               marker=dict(color=RISK_COLOR[r.urgency], line=dict(color="#fff", width=1.5)), text=r.plot_id[-3:], textposition="inside",
                               hovertemplate=f"{r.plot_id}<br>{r.start:%H:%M}–{r.end:%H:%M} ({r.duration_h:.1f} h)<br>{r.volume_m3:,.0f} m³<extra></extra>", showlegend=False))
    f.update_layout(barmode="overlay")
    f.update_xaxes(type="date", tickformat="%H:%M\n%d %b")
    f.update_yaxes(autorange="reversed")
    return style(f, 120 + 55 * df.pump.nunique(), legend=False)


def bar_compare(x, y, title, ytitle, color=None, text=None) -> go.Figure:
    f = go.Figure(go.Bar(x=x, y=y, marker_color=color or C["forest2"], text=text, textposition="outside"))
    f.update_yaxes(title=ytitle, range=[0, float(max(y)) * 1.18])
    f.update_layout(title=dict(text=title, font=dict(size=13)))
    return style(f, 280, legend=False)
