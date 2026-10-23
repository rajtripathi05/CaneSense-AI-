"""Capture screenshots of the running app (real browser, real app). Usage:
python scripts/screenshots.py [--base http://localhost:8501] [--out docs/screenshots] [--width 1440 --height 900] [--pages overview,...]
Also reports Streamlit exception banners and horizontal overflow per page."""
import argparse
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGES = ["overview", "farm-intelligence", "farm-map", "advisor", "scenario-simulator", "operations", "reports", "cloud-lab", "methodology"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8501")
    ap.add_argument("--out", default="docs/screenshots")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--pages", default=",".join(PAGES))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": a.width, "height": a.height})
        for name in a.pages.split(","):
            pg.goto(f"{a.base}/{'' if name == 'overview' else name}", wait_until="networkidle")
            pg.wait_for_selector('[data-testid="stMain"]', timeout=20000)
            pg.wait_for_timeout(4500)
            errs = pg.locator('[data-testid="stException"]').count()
            overflow = pg.evaluate("document.querySelector('[data-testid=\"stMain\"]').scrollWidth - document.querySelector('[data-testid=\"stMain\"]').clientWidth")
            broken = pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length")
            pg.screenshot(path=str(out / f"{a.width}_{name}.png"), full_page=a.full)
            print(f"{name:20s} exceptions={errs} h-overflow={overflow}px broken-images={broken}")
            bad += errs
        b.close()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
