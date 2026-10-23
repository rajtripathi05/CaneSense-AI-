"""Central configuration. Environment variables override defaults; no secrets live in code."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
IMAGES = ASSETS / "images"
BRAND = ASSETS / "brand"
MODEL_DIR = ROOT / "models"
EXPERIMENTS = ROOT / "experiments"
EVIDENCE = ROOT / "evidence"

SEED = int(os.getenv("CANESENSE_SEED", "42"))
N_PLOTS = 28
HISTORY_DAYS = 21
SIM_DAYS = 150
REFERENCE_DATE = "2026-03-14"       # fixed synthetic "today" so demos are repeatable
DAILY_WATER_BUDGET_M3 = 20000.0      # shared pumping capacity for the synthetic estate
CLOUD_ENDPOINT = os.getenv("CANESENSE_CLOUD_URL", "").strip()   # optional, never required

APP_NAME = "CaneSense AI"
DESCRIPTOR = "Precision Irrigation Intelligence"

# Academic metadata (used in documentation and the academic report only)
STUDENT = {
    "name": "Raj Tripathi", "roll": "16014223062", "batch": "B1 AIDS", "status": "Final-Year Student",
    "professor": "Sagar Korde",
    "assignment": "Cloud Computing Experiments through Somaiya Vidyavihar AI Use Cases",
    "project": "CaneSense AI: AI-Powered Precision Irrigation Intelligence for Sugarcane Farms",
    "use_case": "KJS-AGR-01",
}
