"""Experiment 8 - FinOps instance-type comparison using the Experiment 7 measurements (same workload, same conditions).

All prices are ASSUMED public on-demand list prices (USD/hour, Linux, a US region) typed in below for illustration. They were
not fetched from a billing API and no cloud account was used: every figure is an ESTIMATE, not an actual charge. Verify prices
with the provider's calculator before using them for decisions.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "experiments" / "results"
HOURS_PER_MONTH = 730
RUNS_PER_DAY = 24          # scenario: hourly model refresh / analytics run
HEADROOM = 1.5             # memory headroom factor over measured peak
USABLE_MEM = 0.85          # fraction of instance memory usable by the workload after OS/runtime

INSTANCES = [  # name, vCPU, GiB, assumed USD/hour
    ("t3.micro", 2, 1, 0.0104), ("t3.small", 2, 2, 0.0208), ("t3.medium", 2, 4, 0.0416), ("c6i.large", 2, 4, 0.0850),
    ("m6i.large", 2, 8, 0.0960), ("c6i.xlarge", 4, 8, 0.1700), ("c6i.2xlarge", 8, 16, 0.3400),
]


def main():
    rs = json.loads((RES / "rightsizing.json").read_text(encoding="utf-8"))
    by_cores = {p["cores"]: p for p in rs["profiles"]}
    peak = max(p["peak_rss_mb"] for p in rs["profiles"])
    rows = []
    for name, vcpu, gib, price in INSTANCES:
        prof = by_cores.get(vcpu)
        if not prof:
            continue
        run_s = prof["median_s"]
        fits = peak * HEADROOM <= gib * 1024 * USABLE_MEM
        per_run = price * run_s / 3600
        rows.append(dict(instance=name, vcpu=vcpu, memory_gib=gib, hourly_usd=price, measured_runtime_s=run_s, memory_fits=bool(fits),
                         monthly_always_on_usd=round(price * HOURS_PER_MONTH, 2), cost_per_run_usd=round(per_run, 6),
                         cost_per_1000_runs_usd=round(per_run * 1000, 3), monthly_workload_usd=round(per_run * RUNS_PER_DAY * 30, 4),
                         runs_per_hour_capacity=round(3600 / run_s, 1)))
    fitting = [r for r in rows if r["memory_fits"]]
    best_cost = min(fitting, key=lambda r: r["cost_per_run_usd"])
    fastest = min(fitting, key=lambda r: r["measured_runtime_s"])
    for r in rows:
        r["note"] = ("cheapest per run among instances that fit memory" if r is best_cost else "fastest among instances that fit memory" if r is fastest
                     else "does not meet the memory headroom rule" if not r["memory_fits"] else "")
    res = dict(
        experiment="Experiment 8 - FinOps and instance-type comparison", generated=datetime.now().isoformat(timespec="seconds"),
        workload=rs["workload"], source="experiments/results/rightsizing.json (same workload and conditions as Experiment 7)",
        assumptions=(f"ESTIMATES ONLY. Hourly prices are assumed on-demand list prices (Linux, US region), not live billing data. Runtimes are the local measurements "
                     f"for the matching vCPU count; real instances will differ (CPU model, burst credits on t3). Memory fit rule: measured peak {peak:.0f} MB x {HEADROOM} "
                     f"<= {int(USABLE_MEM * 100)}% of instance memory. Always-on = {HOURS_PER_MONTH} h/month; workload-based = {RUNS_PER_DAY} runs/day x 30 days billed per second of run time "
                     f"(an idealised on-demand batch model). Storage, network, support and taxes excluded."),
        disclaimer="No cloud account was used. 'Estimated' figures are calculations from assumed prices; they are not actual charges.",
        instances=rows, best_cost_per_run=best_cost["instance"], fastest=fastest["instance"],
        recommendation=(f"For this workload the cheapest suitable choice is {best_cost['instance']} (est. ${best_cost['cost_per_1000_runs_usd']}/1,000 runs); "
                        f"{fastest['instance']} is fastest ({fastest['measured_runtime_s']} s) but costs more per run because speed-up is sub-linear."))
    (RES / "finops.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    import pandas as pd
    pd.DataFrame(rows).to_csv(RES / "finops.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.5), dpi=150)
    n = [r["instance"] for r in rows]
    cols = ["#1D5A41" if r["memory_fits"] else "#C5392B" for r in rows]
    ax[0].bar(n, [r["monthly_always_on_usd"] for r in rows], color=cols); ax[0].set_title("Est. monthly cost, always on (USD)", fontsize=9)
    ax[1].bar(n, [r["cost_per_1000_runs_usd"] for r in rows], color=cols); ax[1].set_title("Est. cost per 1,000 runs (USD)", fontsize=9)
    ax[2].scatter([r["measured_runtime_s"] for r in rows], [r["cost_per_1000_runs_usd"] for r in rows], c=cols, s=60)
    for r in rows:
        ax[2].annotate(r["instance"], (r["measured_runtime_s"], r["cost_per_1000_runs_usd"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax[2].set_xlabel("runtime (s)", fontsize=8); ax[2].set_title("Cost vs speed (red = fails memory rule)", fontsize=9)
    for a in ax:
        a.tick_params(labelsize=7); a.spines[["top", "right"]].set_visible(False)
    for a in ax[:2]:
        a.tick_params(axis="x", rotation=40)
    fig.tight_layout(); fig.savefig(RES / "finops.png")
    print(json.dumps({k: res[k] for k in ("best_cost_per_run", "fastest", "recommendation")}, indent=1))
    for r in rows:
        print(f"{r['instance']:12s} {r['vcpu']}vCPU {r['memory_gib']:>2}GiB ${r['hourly_usd']:.4f}/h run {r['measured_runtime_s']:.2f}s fits={r['memory_fits']} ${r['monthly_always_on_usd']:.2f}/mo ${r['cost_per_1000_runs_usd']:.3f}/1000 runs")


if __name__ == "__main__":
    sys.exit(main())
