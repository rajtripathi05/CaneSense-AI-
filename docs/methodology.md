# CaneSense AI — Methodology

Academic mini-project by **Raj Tripathi** (Roll 16014223062, Batch B1 AIDS) for Prof. **Sagar Korde** — *Cloud Computing Experiments through Somaiya Vidyavihar AI Use Cases*, use case **KJS-AGR-01**.

## 1. Dataset (synthetic)

`canesense/data.py` simulates **28 plots in 6 fictional villages** (4,200 plot-day rows over 150 days, seed 42).

- Each plot has crop stage, variety, soil type (water-holding capacity), irrigation system (drip / sprinkler / furrow), area, synthetic coordinates and a sensor with battery level.
- Daily water balance: soil moisture (% VWC) decreases with evapotranspiration (ET0) divided by a soil-capacity factor, increases with village-level rain events, and jumps at each plot's irrigation cycle (6–11 day interval, random phase).
- Weather follows a seasonal air-temperature curve with noise; humidity and ET0 are derived from temperature.
- The last day is the *current snapshot* (a fixed forecast gives two villages rain); the last 21 days feed the trend charts.
- `validate_frame` rejects out-of-range values, duplicate plot IDs, unknown stages and missing columns. A missing moisture value (sensor outage) is allowed and handled.

**Labels.** Urgency (Low / Medium / High) is computed from a water-stress score: crop-stage trigger (e.g. grand growth 33%, ripening 21% VWC), ET0, temperature, rain, days since irrigation, soil capacity, plus Gaussian noise (σ = 1.1). These are *synthetic ground truth*, not field observations.

## 2. Machine-learning model

- **Model:** `RandomForestClassifier` (300 trees, max depth 12, min leaf 2, balanced class weights), 10 input features.
- **Split:** stratified 75/25 train/test (3,150 / 1,050 rows), seed 42; plus 5-fold cross-validation of macro-F1.
- **Metrics (computed by `scripts/train_model.py`, stored in `models/metrics.json`):**

| Metric (test set) | Value |
|---|---|
| Accuracy | 0.927 |
| Precision (macro) | 0.875 |
| Recall (macro) | 0.918 |
| F1 (macro) | 0.895 |
| 5-fold CV macro-F1 | 0.840 ± 0.017 |

Per class F1: Low 0.962, Medium 0.805, High 0.918. Soil moisture is the dominant feature (importance 0.61).

**Interpretation.** The scores show the model recovers the synthetic labelling rule from noisy inputs. They are **not** evidence of accuracy on real farms, and no real-farm validation was performed. The Medium class is hardest because it sits between two noisy thresholds.

## 3. Recommendation engine (`engine.py`)

Separate from the model and fully inspectable:

1. Offline sensor → *Sensor readings need review* (no water quantity).
2. Low urgency → *Monitor conditions*.
3. High/Medium urgency with ≥ 10 mm forecast rain in 48 h → *Rainfall adjustment recommended*.
4. High urgency → *Irrigate soon*; Medium → *Monitor conditions*.
5. Net depth = (trigger + 6 pts − moisture) × root-zone depth, capped at 75 mm, minus 0.7 × forecast rain; gross depth = net ÷ system efficiency (0.90 / 0.75 / 0.60).
6. Volume (m³) = gross depth (mm) × area (ha) × 10. Duration (h) = gross depth ÷ application rate (4 / 6 / 10 mm/h).
7. Priority = 75% P(high) + 25% P(medium) + moisture deficit + area. A shared daily budget (20,000 m³, 40% in the restricted scenario) is allocated in priority order; remaining plots become *Restricted water availability*.

## 4. Scenarios

Deterministic transformations of the snapshot, after which the model and engine re-run on all plots: Normal, Dry Spell, Heatwave, Rain Expected, Low Soil Moisture, Sensor Failure (every 4th plot offline, every 7th degraded), Water Availability Restricted. Computed effect on the baseline (28 plots):

| Scenario | High-urgency plots | Need irrigation | Water demand (m³) | Deferred by budget |
|---|---|---|---|---|
| Normal | 10 | 13 | 16,807 | 0 |
| Dry Spell | 21 | 21 | 35,436 | 10 |
| Heatwave | 12 | 15 | 21,271 | 2 |
| Rain Expected | 10 | 18 (all rain-adjusted) | 12,928 | 0 |
| Low Soil Moisture | 27 | 27 | 46,754 | 13 |
| Sensor Failure | 10 | 9 | 10,232 | 0 (7 sensor reviews) |
| Water Restricted | 10 | 13 | 16,807 | 7 |

## 5. Testing

`pytest` (23 tests) covers reproducibility, validation, the train/test split and metrics, probability sums, missing sensor handling, each scenario's expected direction, budget limits, PDF/CSV/Excel contents, Kubernetes manifest structure, Dockerfile contents, asset presence and a Streamlit smoke test. Browser-level checks were run with Playwright against the real app at 1440, 1280, 1024, 768 and 390 px (no exceptions, no horizontal overflow, no broken images).

## 6. Limitations and privacy

- Synthetic data, no real validation; simplified agronomy (no crop-coefficient curve, no soil-water forecasting, no weather API).
- Planning constants (efficiencies, application rates, 75 mm cap) are illustrative.
- Pump schedules and status changes are simulations; the app never controls hardware.
- No personal or farm data is collected; session state stays in memory. Village names are fictional; coordinates are arbitrary.

## 7. Future work

Field validation with real sensor data, crop-coefficient based water balance, live weather forecasts, per-plot calibration, user accounts, and a managed cloud deployment with CI/CD.
