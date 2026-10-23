"""Streamlit session state: one place for the active scenario, history, simulated actions and selections."""
from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
from . import service, scenarios


@st.cache_data(show_spinner=False)
def _frame(name: str, overrides: tuple) -> pd.DataFrame:
    # Pure function of its arguments (deterministic presets), so caching cannot leak mutable scenario state.
    return service.scenario_frame(name, overrides)


@st.cache_data(show_spinner=False)
def _history(name: str, overrides: tuple) -> pd.DataFrame:
    return service.moisture_history(name, overrides)


def init() -> None:
    ss = st.session_state
    ss.setdefault("scenario", scenarios.NORMAL)
    ss.setdefault("history", [])          # scenario event log (newest last)
    ss.setdefault("overrides", {})        # plot_id -> mm applied via simulated "complete" actions
    ss.setdefault("ops_status", {})       # plot_id -> Pending/Scheduled/Completed/Deferred
    ss.setdefault("selected_plot", None)
    ss.setdefault("preview", None)
    ss.setdefault("last_change", None)
    ss.setdefault("report", None)


def overrides_key() -> tuple:
    return tuple(sorted(st.session_state.overrides.items()))


def frame() -> pd.DataFrame:
    return _frame(st.session_state.scenario, overrides_key())


def history() -> pd.DataFrame:
    return _history(st.session_state.scenario, overrides_key())


def frame_for(name: str) -> pd.DataFrame:
    return _frame(name, ())


def baseline_frame() -> pd.DataFrame:
    return _frame(scenarios.NORMAL, ())


def apply_scenario(name: str) -> dict:
    """Switch scenario, log a timestamped event and return a before/after change summary."""
    ss = st.session_state
    before = service.summary(frame())
    ss.scenario, ss.overrides, ss.ops_status = name, {}, {}
    after = service.summary(frame())
    change = dict(scenario=name, before=before, after=after, time=datetime.now().strftime("%H:%M:%S"))
    ss.history.append(dict(Time=change["time"], Scenario=name,
                           **{"High-risk plots": f"{before['high_risk']} → {after['high_risk']}",
                              "Need irrigation": f"{before['need_irrigation']} → {after['need_irrigation']}",
                              "Water demand (m³)": f"{before['demand_m3']:,.0f} → {after['demand_m3']:,.0f}"}))
    ss.last_change, ss.preview = change, None
    return change


def reset() -> dict:
    return apply_scenario(scenarios.NORMAL)


def select_plot(pid: str | None) -> None:
    st.session_state.selected_plot = pid
