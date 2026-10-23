# CaneSense AI — Precision Irrigation Intelligence

AI-assisted irrigation planning for sugarcane farms. A Streamlit application with a scikit-learn urgency model, a transparent
recommendation engine, a deterministic scenario simulator, an offline farm map, PDF/CSV/Excel reporting, and four cloud-computing
experiments (Docker, Kubernetes, right-sizing, FinOps).

> **All farms, plots, sensor readings and labels are synthetic.** The model is trained on synthetic labels and has **not** been
> validated on real sugarcane farms. Outputs are decision support, not agronomic advice.

## Project information

| | |
|---|---|
| **Student** | Raj Tripathi |
| **Roll number** | 16014223062 |
| **Batch** | B1 AIDS |
| **Academic status** | Final-Year Student |
| **Subject / assignment** | Cloud Computing Experiments through Somaiya Vidyavihar AI Use Cases |
| **Project title** | CaneSense AI: AI-Powered Precision Irrigation Intelligence for Sugarcane Farms |
| **Use case ID** | KJS-AGR-01 |
| **Professor / faculty evaluator** | Sagar Korde |

This is the academic mini-project submitted by Raj Tripathi for the Cloud Computing assignment above.

## Quick start (Windows)

Requires Python 3.10+ (developed on 3.11). No internet, cloud credentials, paid APIs or hardware are needed after installing dependencies.

```powershell
# one step: creates .venv, installs, trains the model, launches the app
powershell -ExecutionPolicy Bypass -File scripts\run_windows.ps1
```

Or manually:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\train_model.py        # optional: the app trains on first run if models/ is empty
.\.venv\Scripts\python -m streamlit run app.py
```

Open <http://localhost:8501>. If you already have the dependencies installed: `python -m streamlit run app.py`.

## What is inside

| Page | What it does |
|---|---|
| Overview | Hero, five executive KPIs computed from the data, field map, priority queue, moisture trend, urgency by village, weather/rain |
| Farm Intelligence | Searchable/filterable plot table, export, plot detail with history, AI prediction, recommendation, events, sensor health |
| Farm Map | Offline field-zone map (synthetic coordinates), optional street tiles, filters, selectable plots, linked detail |
| AI Irrigation Advisor | Recommendation cards (action, water, duration, P(high), factors, inputs, limitations) and a what-if form with validation |
| Scenario Simulator | 7 deterministic scenarios, preview, **Apply Scenario**, reset, change summary, timestamped history |
| Irrigation Operations | Priority queue with editable statuses (simulated), pump schedule timeline, action log |
| Reports & Exports | Scope filters, preview, PDF (cover header, charts, repeated-header table, page numbers), CSV, Excel |
| Cloud Lab | Docker / Kubernetes commands and *honest* verification status, right-sizing and FinOps charts from saved results, optional cloud check |
| Methodology | Dataset, model metrics (computed), confusion matrix, rules, limitations |

Every number on the dashboard is computed from the synthetic dataset by the current scenario: `data → scenario → ML model → rule engine`.

## Project layout

```
app.py                  Streamlit entry point (navigation, shell)
views/                  One file per page
canesense/              data, model, engine, scenarios, service, reports, charts, theme, ui, panels, state
assets/images, brand    Local photographs (with IMAGE_CREDITS.md), logo, favicon, social preview
models/                 urgency_rf.joblib + metrics.json (generated)
data/                   Sample synthetic CSVs
scripts/                train_model, benchmark, finops, screenshots, build_deliverables, run_windows.ps1, docker_benchmark.ps1
k8s/                    namespace, configmap, deployment, service, hpa
experiments/results/    rightsizing.json/csv/png, finops.json/csv/png
evidence/               Per-experiment status.json and console logs
docs/                   architecture, methodology, experiment guides, demo script, checklist, screenshots
outputs/                Final deliverables (report PDF, source ZIP, sample farm report, test results)
tests/                  pytest suite
```

## Tests

```powershell
python -m pytest -q
```

The suite covers data generation/validation, model training and inference, engine and scenarios, PDF/CSV/Excel output, Docker/Kubernetes file integrity and an application smoke test.

## Docker and Kubernetes (Experiments 2 and 3)

```powershell
docker build -t canesense-ai:1.0 .
docker run -d --name canesense -p 8501:8501 canesense-ai:1.0
kubectl apply -f k8s/
```

Details: [docs/experiment2_docker.md](docs/experiment2_docker.md) and [docs/experiment3_kubernetes.md](docs/experiment3_kubernetes.md).
**Status on the author's machine:** Docker and kubectl are not installed, so these two experiments are fully prepared but were **not executed**; see `evidence/exp2_docker/status.json` and `evidence/exp3_kubernetes/status.json`.

## Benchmark and FinOps (Experiments 7 and 8)

```powershell
python scripts\benchmark.py --cores 1,2,4,8 --reps 3     # writes experiments/results/rightsizing.*
python scripts\finops.py                                   # writes experiments/results/finops.*
```

Both were executed; results are in `experiments/results/` and summarised in [docs/experiment7_rightsizing.md](docs/experiment7_rightsizing.md) and [docs/experiment8_finops.md](docs/experiment8_finops.md).

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `CANESENSE_SEED` | Dataset seed (changing it changes the synthetic estate) | `42` |
| `CANESENSE_CLOUD_URL` | Optional HTTP health endpoint for the Cloud Lab connection check | unset → "not configured" |

No secrets are stored in the code.

## Image credits

Photographs are stored locally in `assets/images/` and credited in [assets/IMAGE_CREDITS.md](assets/IMAGE_CREDITS.md).

## Known limitations

- Synthetic data and labels; model metrics reflect recovery of a synthetic rule, not real-world accuracy.
- Street-tile map mode needs internet (the offline field-zone view is the default).
- The benchmark emulates vCPU profiles with CPU affinity on one machine; FinOps figures use assumed list prices and are estimates, not charges.
- Docker / Kubernetes steps are documented but unverified on this machine (no Docker, no cluster).
- AI-assisted development: this project was built with the assistance of Claude (Anthropic) and reviewed/run by the student.
