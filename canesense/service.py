"""Framework-free pipeline: baseline -> scenario -> ML prediction -> recommendations."""
from __future__ import annotations
from functools import lru_cache
import pandas as pd
from . import scenarios
from .config import SEED
from .data import build_baseline, STAGE_ROOT_MM
from .engine import recommend, kpis
from .model import load_or_train, predict


@lru_cache(maxsize=4)
def baseline(seed: int = SEED) -> dict:
    return build_baseline(seed)


@lru_cache(maxsize=1)
def model_bundle():
    return load_or_train()


def scenario_frame(name: str, overrides: tuple = (), seed: int = SEED) -> pd.DataFrame:
    """Full per-plot recommendation table for a scenario. `overrides` = ((plot_id, applied_mm), ...)
    simulating completed irrigation events. Pure: never mutates cached baselines."""
    b = baseline(seed)
    snap = scenarios.apply(b["current"], name)
    for pid, mm in overrides:
        m = snap.plot_id == pid
        root = STAGE_ROOT_MM[snap.loc[m, "crop_stage"].iloc[0]]
        snap.loc[m, "soil_moisture"] = (snap.loc[m, "soil_moisture"].fillna(25) + mm / root * 100).clip(upper=50)
        snap.loc[m, "days_since_irrigation"] = 0
    clf, _ = model_bundle()
    return recommend(predict(clf, snap), water_factor=float(snap.water_factor.iloc[0]))


def summary(df: pd.DataFrame) -> dict:
    return kpis(df)


def moisture_history(scenario_name: str, overrides: tuple = ()) -> pd.DataFrame:
    """History window with the scenario's relative moisture shift applied to the final day only for continuity."""
    b = baseline()
    h = b["history"].copy()
    cur = scenario_frame(scenario_name, overrides)[["plot_id", "soil_moisture"]].set_index("plot_id")["soil_moisture"]
    last = h.date.max()
    h.loc[h.date == last, "soil_moisture"] = h.loc[h.date == last, "plot_id"].map(cur).values
    return h
