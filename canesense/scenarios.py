"""Deterministic scenario presets applied to the synthetic baseline snapshot and history."""
from __future__ import annotations
import numpy as np
import pandas as pd

NORMAL = "Normal Conditions"

SCENARIOS = {
    NORMAL: dict(icon=":material/check_circle:", tone="green", blurb="Baseline synthetic readings for the estate.",
                 change="No changes. Restores the original readings and forecast."),
    "Simulate Dry Spell": dict(icon=":material/wb_sunny:", tone="amber", blurb="No rain, higher evaporative demand.",
                 change="Moisture falls about 28% (relative), ET0 +1.2 mm/day, humidity -12 pts, rain forecast removed, +3 days since last irrigation."),
    "Simulate Heatwave": dict(icon=":material/device_thermostat:", tone="red", blurb="Sustained high temperatures.",
                 change="Air +6 C, soil +4 C, ET0 +2.5 mm/day, moisture falls about 15% (relative), humidity -15 pts."),
    "Rain Expected": dict(icon=":material/rainy:", tone="blue", blurb="Significant rain forecast within 48 h.",
                 change="Forecast rain set to 28 mm on every village, humidity +15 pts. Moisture unchanged, so advice shifts to rainfall adjustment."),
    "Low Soil Moisture": dict(icon=":material/water_drop:", tone="amber", blurb="Soil moisture drops across the estate.",
                 change="Moisture falls 40% (relative) on all plots with no other weather change."),
    "Sensor Failure": dict(icon=":material/sensors_off:", tone="red", blurb="Field sensors drop out.",
                 change="Every 4th plot (7 plots) goes offline with no moisture reading; every 7th plot is flagged degraded."),
    "Water Availability Restricted": dict(icon=":material/block:", tone="amber", blurb="Pumping capacity cut.",
                 change="Shared daily water budget reduced to 40% of normal; lower-priority plots are deferred."),
}


def apply(snapshot: pd.DataFrame, name: str) -> pd.DataFrame:
    """Return a transformed copy of the baseline snapshot. Pure and deterministic."""
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")
    d = snapshot.copy()
    d["water_factor"] = 1.0
    if name == "Simulate Dry Spell":
        d["soil_moisture"] = (d.soil_moisture * 0.72).round(1)
        d["et0"] += 1.2
        d["humidity"] = (d.humidity - 12).clip(lower=15)
        d["rain_24h"] = 0.0
        d["forecast_rain_48h"] = 0.0
        d["days_since_irrigation"] += 3
    elif name == "Simulate Heatwave":
        d["air_temp"] += 6
        d["soil_temp"] += 4
        d["et0"] += 2.5
        d["soil_moisture"] = (d.soil_moisture * 0.85).round(1)
        d["humidity"] = (d.humidity - 15).clip(lower=15)
    elif name == "Rain Expected":
        d["forecast_rain_48h"] = 28.0
        d["humidity"] = (d.humidity + 15).clip(upper=98)
    elif name == "Low Soil Moisture":
        d["soil_moisture"] = (d.soil_moisture * 0.60).round(1)
    elif name == "Sensor Failure":
        idx = np.arange(len(d))
        off, deg = idx % 4 == 1, (idx % 7 == 3) & (idx % 4 != 1)
        d.loc[off, "sensor_status"] = "Offline"
        d.loc[off, "soil_moisture"] = np.nan
        d.loc[deg, "sensor_status"] = "Degraded"
    elif name == "Water Availability Restricted":
        d["water_factor"] = 0.4
    d["soil_moisture"] = d["soil_moisture"].clip(lower=3)
    return d
