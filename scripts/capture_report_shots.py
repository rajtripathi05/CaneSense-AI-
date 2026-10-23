"""Drive the running app with a real browser and save the screenshots used in the report. Usage:
python scripts/capture_report_shots.py [--base http://localhost:8501]"""
import argparse
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def nav(pg, name, wait=3500):
    pg.get_by_role("link", name=name).first.click()
    pg.wait_for_timeout(wait)


def shot(pg, name, full=False):
    pg.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name, "exceptions:", pg.locator('[data-testid="stException"]').count())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8501")
    a = ap.parse_args()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        pg = ctx.new_page()
        pg.goto(a.base, wait_until="networkidle")
        pg.wait_for_timeout(5000)
        shot(pg, "01_overview_normal")
        pg.mouse.wheel(0, 900); pg.wait_for_timeout(1200)
        shot(pg, "02_overview_trends")
        nav(pg, "Farm Intelligence")
        pg.get_by_placeholder("e.g. CS-P07 or Chandanpur").fill("Jaggery"); pg.keyboard.press("Enter"); pg.wait_for_timeout(2500)
        pg.locator('[data-testid="stDataFrame"]').first.click(position={"x": 22, "y": 52}); pg.wait_for_timeout(2500)
        pg.mouse.wheel(0, 650); pg.wait_for_timeout(1500)
        shot(pg, "03_farm_intelligence_detail")
        nav(pg, "Farm Map")
        pts = pg.locator(".scatterlayer .trace .points path.point")
        pts.nth(8).click(force=True); pg.wait_for_timeout(3500)
        shot(pg, "04_farm_map_selected")
        nav(pg, "AI Irrigation Advisor")
        shot(pg, "05_ai_advisor")
        nav(pg, "Scenario Simulator")
        pg.get_by_role("button", name=re.compile("Preview impact")).nth(1).click(); pg.wait_for_timeout(2500)
        pg.mouse.wheel(0, 300); pg.wait_for_timeout(800)
        shot(pg, "06_simulator_preview_dry_spell")
        pg.get_by_role("button", name=re.compile("Apply Scenario")).click(); pg.wait_for_timeout(5000)
        pg.mouse.wheel(0, 500); pg.wait_for_timeout(1000)
        shot(pg, "07_simulator_applied")
        nav(pg, "Overview", 4500)
        shot(pg, "08_overview_dry_spell")
        nav(pg, "Irrigation Operations")
        pg.get_by_role("tab", name="Suggested pump schedule").click(); pg.wait_for_timeout(2500)
        shot(pg, "09_operations_schedule")
        nav(pg, "Reports & Exports")
        pg.get_by_role("button", name=re.compile("Generate PDF")).click(); pg.wait_for_timeout(5000)
        shot(pg, "10_reports")
        with pg.expect_download() as d:
            pg.get_by_role("button", name=re.compile("Download PDF")).click()
        d.value.save_as(str(ROOT / "outputs" / "CaneSense_Farm_Operations_Report_DrySpell.pdf"))
        print("saved farm operations PDF from the running app")
        nav(pg, "Cloud Lab")
        shot(pg, "11_cloud_lab")
        pg.get_by_role("tab", name="Right-sizing").click(); pg.wait_for_timeout(3000)
        shot(pg, "12_cloud_rightsizing")
        pg.get_by_role("tab", name="FinOps").click(); pg.wait_for_timeout(3000)
        shot(pg, "13_cloud_finops")
        nav(pg, "Methodology")
        pg.get_by_role("tab", name="Model & metrics").click(); pg.wait_for_timeout(3000)
        shot(pg, "14_methodology_metrics")
        # restore baseline
        nav(pg, "Scenario Simulator")
        pg.get_by_role("button", name=re.compile("Preview impact")).nth(0).click(); pg.wait_for_timeout(2000)
        pg.get_by_role("button", name=re.compile("Reset to Normal")).click(); pg.wait_for_timeout(4000)
        b.close()


if __name__ == "__main__":
    main()
