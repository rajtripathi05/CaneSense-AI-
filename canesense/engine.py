"""Transparent, rule-based irrigation recommendation engine layered on top of the ML urgency prediction."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .config import DAILY_WATER_BUDGET_M3
from .data import IRRIGATION, STAGE_ROOT_MM

A_IRRIGATE = "Irrigate soon"
A_MONITOR = "Monitor conditions"
A_RAIN = "Rainfall adjustment recommended"
A_RESTRICT = "Restricted water availability"
A_SENSOR = "Sensor readings need review"
ACTIONS = [A_IRRIGATE, A_RAIN, A_RESTRICT, A_SENSOR, A_MONITOR]

MAX_EVENT_MM = 75.0
RAIN_EFFECTIVE = 0.7
RAIN_SKIP_MM = 10.0

EXPLAIN = {
    A_IRRIGATE: "Soil moisture is below the crop-stage trigger and no meaningful rain is forecast. Irrigate within 24 hours.",
    A_MONITOR: "Conditions are acceptable right now. Keep watching moisture and re-check after the next reading.",
    A_RAIN: "Irrigation is indicated, but forecast rain will supply part of the demand. Reduce or delay the event and re-check after the rain.",
    A_RESTRICT: "Irrigation is indicated but the shared water budget is exhausted for this plot. Defer or use the reduced allocation.",
    A_SENSOR: "The moisture sensor is offline, so the model estimate relies on a village median. Inspect the sensor before irrigating.",
}


def _row_reco(r: pd.Series) -> dict:
    eff, rate = IRRIGATION[r.irrigation_type]
    offline = r.sensor_status == "Offline"
    target = r.stage_threshold + 6
    moist = r.soil_moisture if not np.isnan(r.soil_moisture) else target - 8
    deficit_pts = max(0.0, target - moist)
    net_mm = min(MAX_EVENT_MM, deficit_pts / 100 * STAGE_ROOT_MM[r.crop_stage])
    net_after_rain = max(0.0, net_mm - RAIN_EFFECTIVE * r.forecast_rain_48h)
    needs = r.urgency in ("High", "Medium")
    if offline:
        action = A_SENSOR
    elif r.urgency == "Low":
        action = A_MONITOR
    elif r.forecast_rain_48h >= RAIN_SKIP_MM:
        action = A_RAIN
    elif r.urgency == "High":
        action = A_IRRIGATE
    else:
        action = A_MONITOR
    use_mm = net_after_rain if action in (A_IRRIGATE, A_RAIN, A_RESTRICT) else 0.0
    gross_mm = use_mm / eff
    volume = gross_mm * r.area_ha * 10.0
    hours = gross_mm / rate
    factors = []
    gap = r.stage_threshold - moist
    if not offline:
        factors.append(f"Moisture {moist:.1f}% is {'below' if gap > 0 else 'above'} the {r.crop_stage.lower()} trigger of {r.stage_threshold}% by {abs(gap):.1f} pts")
    factors.append(f"ET0 {r.et0:.1f} mm/day and air temperature {r.air_temp:.1f} °C")
    factors.append(f"{r.days_since_irrigation} day(s) since last irrigation")
    factors.append(f"Forecast rain {r.forecast_rain_48h:.0f} mm in 48 h" if r.forecast_rain_48h > 0 else "No rain forecast in 48 h")
    priority = 100 * (0.75 * r.p_high + 0.25 * r.p_medium) + min(15.0, deficit_pts) + 0.5 * r.area_ha
    if offline:
        priority = min(priority, 55.0)
    return dict(action=action, depth_mm=round(gross_mm, 1), volume_m3=round(volume, 0), duration_h=round(hours, 1),
                factors=" | ".join(factors), priority=round(priority, 1), explanation=EXPLAIN[action],
                data_quality=("Sensor offline - value estimated" if offline else
                              "Sensor degraded (low battery) - verify reading" if r.sensor_status == "Degraded" else "OK"))


def recommend(pred: pd.DataFrame, water_factor: float = 1.0, budget_m3: float = DAILY_WATER_BUDGET_M3) -> pd.DataFrame:
    """Turn model output into actions, quantities and a water-budget allocation (highest priority first)."""
    out = pred.copy()
    recs = pd.DataFrame([_row_reco(r) for _, r in out.iterrows()], index=out.index)
    out = pd.concat([out, recs], axis=1)
    cap = budget_m3 * float(water_factor)
    out = out.sort_values("priority", ascending=False)
    used, alloc = 0.0, []
    for _, r in out.iterrows():
        if r.action in (A_IRRIGATE, A_RAIN):
            if used + r.volume_m3 <= cap:
                used += r.volume_m3
                alloc.append(r.volume_m3)
            else:
                alloc.append(0.0)
        else:
            alloc.append(0.0)
    out["allocated_m3"] = alloc
    restricted = (out.action.isin([A_IRRIGATE, A_RAIN])) & (out.allocated_m3 == 0) & (out.volume_m3 > 0)
    out.loc[restricted, "action"] = A_RESTRICT
    out.loc[restricted, "explanation"] = EXPLAIN[A_RESTRICT]
    out["rank"] = np.arange(1, len(out) + 1)
    out.attrs["budget_m3"], out.attrs["used_m3"] = cap, used
    return out.sort_index()


def kpis(df: pd.DataFrame) -> dict:
    act = df[df.action.isin([A_IRRIGATE, A_RAIN, A_RESTRICT])]
    return dict(
        farms=int(df.village.nunique()), plots=int(len(df)), area_ha=float(df.area_ha.sum()),
        need_irrigation=int(len(act)), high_risk=int((df.urgency == "High").sum()),
        medium_risk=int((df.urgency == "Medium").sum()), low_risk=int((df.urgency == "Low").sum()),
        demand_m3=float(df.volume_m3.sum()), allocated_m3=float(df.allocated_m3.sum()),
        sensors_online=int((df.sensor_status == "Online").sum()), sensors_degraded=int((df.sensor_status == "Degraded").sum()),
        sensors_offline=int((df.sensor_status == "Offline").sum()),
        mean_moisture=float(df.soil_moisture.mean(skipna=True)), restricted=int((df.action == A_RESTRICT).sum()),
        review=int((df.action == A_SENSOR).sum()), rain_adjust=int((df.action == A_RAIN).sum()),
    )
