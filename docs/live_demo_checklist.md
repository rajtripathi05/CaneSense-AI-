# CaneSense AI — Live Demo Checklist

Presenter: Raj Tripathi · Roll 16014223062 · Batch B1 AIDS · Prof. Sagar Korde · Use case KJS-AGR-01

## Before you start (5 minutes)
- [ ] `python -m pytest -q` shows all tests passing
- [ ] `python -m streamlit run app.py` running; <http://localhost:8501> loads without a red error box
- [ ] Browser window 1440×900, zoom 100%, bookmarks bar hidden, notifications off
- [ ] Sidebar visible; header chips read *Demo mode · synthetic data*, *System healthy*, *Scenario: Normal Conditions*
- [ ] Hero photograph visible (no broken image); map shows 28 markers
- [ ] `outputs/` folder open in a second window for the PDF/Excel downloads
- [ ] Internet off is fine — nothing in the core demo needs it (street-tile map toggle excluded)

## Demo flow
1. [ ] **Overview** — read the five KPIs (13 need irrigation, 10 high-risk, 16,807 m³, 27/28 sensors)
2. [ ] Click a plot on the map; mention shape + colour for risk
3. [ ] **Farm Intelligence** — search `Jaggery`, select a row, show history chart, prediction, recommendation, sensor health
4. [ ] **AI Irrigation Advisor** — open a card, explain model vs rule engine, note the limitations line
5. [ ] **Scenario Simulator** — Preview **Simulate Dry Spell** (10 → 21 high, 35,436 m³) → **Apply Scenario**
6. [ ] **Overview** again — KPIs, map colours and queue changed
7. [ ] Simulator → **Rain Expected** → Apply (rainfall-adjustment advice, 12,928 m³)
8. [ ] Simulator → **Sensor Failure** → Apply (7 offline; Farm Intelligence shows *Sensor readings need review*)
9. [ ] **Irrigation Operations** — set a plot to *Completed*, **Apply status changes**, show moisture/KPI effect
10. [ ] **Reports & Exports** — choose a village, **Generate PDF report**, download PDF, CSV, Excel; open the PDF
11. [ ] **Cloud Lab** — show the four status cards (2 and 3 *not executed*, 7 and 8 *executed*), right-sizing and FinOps charts
12. [ ] **Methodology** — metrics, confusion matrix, limitations
13. [ ] Simulator → **Reset to Normal**

## If something goes wrong
| Symptom | Fix |
|---|---|
| Page shows an error box | Refresh the browser tab; state resets to Normal |
| Scenario seems stuck | Simulator → *Reset to Normal* |
| Map blank in Street-tiles mode | Switch to *Field-zone (offline)* |
| Port 8501 busy | `python -m streamlit run app.py --server.port 8502` |
| Model missing | `python scripts\train_model.py` |

## Honesty reminders
- Say "synthetic" when showing any number. Do not call the model accurate on real farms.
- Say "estimated" for all costs. Say Docker and Kubernetes were **not executed** on this machine.
