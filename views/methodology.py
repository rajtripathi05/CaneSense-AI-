import json

import streamlit as st

from canesense import charts, state, ui
from canesense.config import MODEL_DIR, ROOT, STUDENT, IMAGES
from canesense.data import FEATURES, STAGE_THRESHOLD, SIM_DAYS, HISTORY_DAYS
from canesense.theme import data_uri

ui.shell("Methodology", "Dataset, model, assumptions, testing and limitations")
mp = MODEL_DIR / "metrics.json"
m = json.loads(mp.read_text()) if mp.exists() else None

ui.md(f"<div class='cs-card'>Academic mini-project by <b>{STUDENT['name']}</b> (roll no. {STUDENT['roll']}, {STUDENT['batch']}), submitted to Prof. {STUDENT['professor']} for "
      f"<i>{STUDENT['assignment']}</i>. Use case {STUDENT['use_case']}.</div>")

t1, t2, t3, t4 = st.tabs(["Dataset", "Model & metrics", "Recommendation engine", "Testing & limitations"])
with t1:
    a, b = st.columns([3, 2])
    with a:
        st.markdown(f"""
**Fully synthetic.** `canesense/data.py` simulates **28 plots in 6 fictional villages** with a daily water balance over **{SIM_DAYS} days** (4,200 plot-day rows, seed 42).

- Soil moisture drains with evapotranspiration (ET0) scaled by soil water-holding capacity, rises with rain and with a plot-specific irrigation cycle.
- Weather (air temperature, humidity, ET0) follows a seasonal curve with noise; rain events are random per village but fixed by the seed.
- The latest day is the *current snapshot*; the last {HISTORY_DAYS} days feed charts. Coordinates are arbitrary points in a fictional layout.
- Sensor status and battery are simulated. Nothing here belongs to a real farm or farmer.

**Labels** (Low / Medium / High urgency) come from an agronomic water-stress score using crop-stage triggers ({', '.join(f'{k} {v}%' for k, v in STAGE_THRESHOLD.items())}), ET0, temperature,
rain and days since irrigation, plus Gaussian noise. They are therefore *synthetic ground truth*.""")
    with b:
        uri = data_uri("hero_sugarcane_1500.jpg")
        sensor = IMAGES / "soil_sensor.jpg"
        if sensor.exists():
            st.image(str(sensor), caption="Soil-moisture sensor probe (CC0, Christianjhart1 / Wikimedia Commons)")
with t2:
    if not m:
        ui.empty("Metrics not available", "Run `python scripts/train_model.py` to train the model and write models/metrics.json.")
    else:
        c = st.columns(5)
        for col, (lab, val) in zip(c, [("Accuracy", m["accuracy"]), ("Precision (macro)", m["precision_macro"]), ("Recall (macro)", m["recall_macro"]),
                                       ("F1 (macro)", m["f1_macro"]), ("5-fold CV F1", m["cv_f1_macro_mean"])]):
            col.metric(lab, f"{val:.3f}")
        st.caption(f"RandomForest (300 trees), stratified 75/25 split: {m['n_train']:,} train / {m['n_test']:,} test rows. 5-fold CV F1 std ±{m['cv_f1_macro_std']:.3f}. {m['note']}")
        a, b = st.columns(2)
        with a:
            st.markdown("**Confusion matrix (test set)**")
            st.plotly_chart(charts.confusion(m["confusion_matrix"], m["classes"]), width="stretch", config={"displayModeBar": False}, key="mth_cm")
        with b:
            st.markdown("**Feature importance**")
            st.plotly_chart(charts.importance(m["feature_importance"]), width="stretch", config={"displayModeBar": False}, key="mth_fi")
        st.dataframe([{"Class": k, **{kk: round(vv, 3) for kk, vv in v.items()}} for k, v in m["per_class"].items()], hide_index=True, width="stretch")
with t3:
    st.markdown("""
| Step | Rule |
|---|---|
| Sensor check | Offline sensor → *Sensor readings need review* (moisture imputed from village median for the model only) |
| Low urgency | *Monitor conditions* |
| Rain forecast ≥ 10 mm / 48 h with High/Medium urgency | *Rainfall adjustment recommended* |
| High urgency | *Irrigate soon* |
| Water depth | (trigger + 6 pts − moisture) × root-zone depth, ≤ 75 mm, − 0.7 × forecast rain, ÷ system efficiency (drip 0.90, sprinkler 0.75, furrow 0.60) |
| Volume / duration | depth × area × 10 (m³); depth ÷ application rate (drip 4, sprinkler 6, furrow 10 mm/h) |
| Budget | Priority-ordered allocation of a shared daily budget; overflow → *Restricted water availability* |

Scenarios are deterministic transformations of the baseline snapshot (see the Scenario Simulator), after which the **model and engine are re-run** on every plot.""")
with t4:
    tr = ROOT / "outputs" / "test_results.txt"
    st.markdown("**Automated tests** (`pytest`) cover data generation and validation, model training/inference, the engine, scenarios, report generation, and Docker/Kubernetes file integrity.")
    if tr.exists():
        st.code(tr.read_text(encoding="utf-8")[-1500:], language="text")
    st.markdown("""
**Limitations**
- Synthetic data and labels: metrics show the model reproduces the generating rule, not real-world accuracy. No field validation has been done.
- Single-snapshot decisions; no crop-coefficient curve, soil-water-balance forecasting or weather API.
- Water depth, efficiency and flow figures are simplified planning constants.
- Pump schedule and statuses are simulations; the app never controls hardware.

**Privacy:** no personal or farm data is collected or stored; all state lives in the browser session.""")
