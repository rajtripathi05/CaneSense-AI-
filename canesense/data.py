"""Reproducible synthetic dataset: 28 plots, daily observations, validation helpers."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .config import SEED, SIM_DAYS, HISTORY_DAYS, REFERENCE_DATE

# Fictional villages (synthetic) arranged around an arbitrary point in the Western Maharashtra sugar belt.
VILLAGES = {
    "Amravanti Wadi": (16.880, 74.520, "Black clay"),
    "Chandanpur":     (16.880, 74.575, "Alluvial loam"),
    "Devgad Khurd":   (16.845, 74.500, "Red loam"),
    "Harsulwadi":     (16.845, 74.555, "Black clay"),
    "Jaggery Nagar":  (16.815, 74.525, "Sandy loam"),
    "Kaneri Pada":    (16.815, 74.580, "Alluvial loam"),
}
SOIL_WHC = {"Black clay": 1.0, "Alluvial loam": 0.85, "Red loam": 0.7, "Sandy loam": 0.5}  # relative holding capacity
STAGES = ["Germination", "Tillering", "Grand growth", "Maturity", "Ripening"]
STAGE_THRESHOLD = {"Germination": 31, "Tillering": 29, "Grand growth": 33, "Maturity": 26, "Ripening": 21}  # VWC % trigger
STAGE_ROOT_MM = {"Germination": 250, "Tillering": 400, "Grand growth": 700, "Maturity": 800, "Ripening": 600}
IRRIGATION = {"Drip": (0.90, 4.0), "Sprinkler": (0.75, 6.0), "Furrow": (0.60, 10.0)}  # (efficiency, mm/h)
FEATURES = ["soil_moisture", "soil_temp", "air_temp", "humidity", "rain_24h", "forecast_rain_48h",
            "et0", "days_since_irrigation", "stage_threshold", "soil_whc"]

REQUIRED_COLUMNS = ["plot_id", "village", "soil_moisture", "soil_temp", "air_temp", "humidity", "rain_24h",
                    "forecast_rain_48h", "et0", "days_since_irrigation", "crop_stage", "soil_type"]
RANGES = {"soil_moisture": (0, 60), "soil_temp": (5, 55), "air_temp": (0, 50), "humidity": (0, 100),
          "rain_24h": (0, 300), "forecast_rain_48h": (0, 300), "et0": (0, 15), "days_since_irrigation": (0, 60)}


def validate_frame(df: pd.DataFrame) -> list[str]:
    """Return human-readable problems (empty list = valid). Missing moisture is allowed (sensor outage)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return [f"Missing required column(s): {', '.join(missing)}."]
    problems = []
    for col, (lo, hi) in RANGES.items():
        bad = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        if bad.any():
            problems.append(f"{col}: {int(bad.sum())} value(s) outside the plausible range {lo}-{hi}.")
    if df["plot_id"].duplicated().any():
        problems.append("Duplicate plot_id values found.")
    unknown = set(df["crop_stage"]) - set(STAGES)
    if unknown:
        problems.append(f"Unknown crop stage(s): {', '.join(sorted(unknown))}.")
    return problems


def make_plots(rng: np.random.Generator) -> pd.DataFrame:
    counts = [5, 5, 5, 5, 4, 4]
    rows, n = [], 0
    for (v, (lat0, lon0, soil)), c in zip(VILLAGES.items(), counts):
        for k in range(c):
            n += 1
            gx, gy = k % 3, k // 3
            rows.append(dict(
                plot_id=f"CS-P{n:02d}", village=v,
                lat=round(lat0 + (0.5 - gy) * 0.016 + rng.normal(0, 0.0015), 5),
                lon=round(lon0 + (gx - 1) * 0.0155 + rng.normal(0, 0.0015), 5),
                area_ha=round(float(rng.uniform(0.8, 3.2)), 1),
                crop_stage=str(rng.choice(STAGES, p=[0.1, 0.2, 0.4, 0.2, 0.1])),
                variety=str(rng.choice(["Co 86032", "CoM 0265", "Co 0238", "CoVC 18061"])),
                soil_type=soil, irrigation_type=str(rng.choice(list(IRRIGATION), p=[0.4, 0.3, 0.3])),
                interval=int(rng.integers(6, 12)), phase=int(rng.integers(0, 11)),
                sensor_id=f"SN-{1000 + n * 7}", battery_pct=int(rng.integers(35, 100)),
            ))
    return pd.DataFrame(rows)


def simulate(seed: int = SEED, n_days: int = SIM_DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (plots, observations). Observations are daily water-balance simulations per plot."""
    rng = np.random.default_rng(seed)
    plots = make_plots(rng)
    dates = pd.date_range(end=REFERENCE_DATE, periods=n_days, freq="D")
    doy = dates.dayofyear.values
    base_t = 29 + 4 * np.sin((doy - 60) / 365 * 2 * np.pi)
    vrain = {v: np.where(rng.random(n_days) < 0.12, rng.gamma(2.0, 7.0, n_days), 0.0) for v in VILLAGES}
    for v in VILLAGES:
        vrain[v][-1] = 0.0                      # final 24 h dry
    air = base_t + rng.normal(0, 1.8, n_days)
    hum = np.clip(60 - (air - 29) * 3 + rng.normal(0, 6, n_days), 25, 95)
    et0 = np.clip(4.2 + (air - 29) * 0.35 + rng.normal(0, 0.4, n_days), 1.5, 9)
    fc_now = {v: 0.0 for v in VILLAGES}
    fc_now.update({"Chandanpur": 14.0, "Kaneri Pada": 9.0})   # deterministic baseline forecast
    recs = []
    for _, p in plots.iterrows():
        whc = SOIL_WHC[p.soil_type]
        m = STAGE_THRESHOLD[p.crop_stage] + 8 + rng.normal(0, 2)
        last_irr = -99
        for i in range(n_days):
            m -= (et0[i] * 0.36 + 0.45) / (0.55 + 0.45 * whc)
            if vrain[p.village][i] > 0:
                m += vrain[p.village][i] / 1.6 * whc
            if (i + p.phase) % p.interval == 0:
                m += rng.uniform(11, 15) * (0.8 + 0.2 * whc)
                last_irr = i
            m = float(np.clip(m, 8, 42 + 6 * whc))
            nxt = vrain[p.village][min(i + 1, n_days - 1)]
            recs.append(dict(
                date=dates[i], plot_id=p.plot_id, village=p.village,
                soil_moisture=round(m + rng.normal(0, 0.4), 1),
                soil_temp=round(air[i] - 3.5 + rng.normal(0, 0.8), 1),
                air_temp=round(air[i] + rng.normal(0, 0.5), 1),
                humidity=round(float(hum[i] + rng.normal(0, 2)), 1),
                rain_24h=round(float(vrain[p.village][i]), 1),
                forecast_rain_48h=fc_now[p.village] if i == n_days - 1 else round(float(nxt), 1),
                et0=round(float(et0[i]), 2),
                days_since_irrigation=(i - last_irr) if last_irr >= 0 else 14,
                crop_stage=p.crop_stage, soil_type=p.soil_type,
            ))
    return plots.drop(columns=["interval", "phase"]), pd.DataFrame(recs)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["stage_threshold"] = df["crop_stage"].map(STAGE_THRESHOLD)
    df["soil_whc"] = df["soil_type"].map(SOIL_WHC)
    return df


def label_urgency(df: pd.DataFrame, seed: int = SEED + 1) -> pd.Series:
    """Synthetic ground truth: agronomic water-stress score + noise (NOT a field-validated label)."""
    rng = np.random.default_rng(seed)
    stress = (df.stage_threshold + 0.9 * (df.et0 - 4.2) + 0.2 * (df.air_temp - 29)
              - df.soil_moisture - 0.12 * df.forecast_rain_48h - 0.10 * df.rain_24h
              + 0.15 * df.days_since_irrigation * (1.1 - df.soil_whc))
    stress = stress + rng.normal(0, 1.1, len(df))
    return pd.cut(stress, [-np.inf, -6.0, 2.0, np.inf], labels=["Low", "Medium", "High"]).astype(str)


def build_baseline(seed: int = SEED) -> dict:
    """Plots, history window and the 'current' per-plot snapshot (latest observation + sensor status)."""
    plots, obs = simulate(seed)
    hist = obs[obs.date > obs.date.max() - pd.Timedelta(days=HISTORY_DAYS)].reset_index(drop=True)
    cur = obs[obs.date == obs.date.max()].drop(columns=["date"]).merge(
        plots.drop(columns=["village", "soil_type", "crop_stage"]), on="plot_id")
    cur["sensor_status"] = np.where(cur.battery_pct < 40, "Degraded", "Online")
    cur["water_factor"] = 1.0
    return dict(plots=plots, obs=obs, history=hist, current=cur.reset_index(drop=True))
