"""Experiment 7 - right-sizing benchmark of the CaneSense analytics workload.

Runs the *real* pipeline (simulate -> label -> train RandomForest -> batch inference -> recommendation engine) in a fresh
subprocess per profile, pinned to N CPU cores via OS CPU affinity, and records wall time, per-stage time and peak memory.

Honest scope: this is a local-process emulation of vCPU profiles on the host machine (no hypervisor, no cgroup memory
cap). Memory is *measured* (peak working set), not limited. See docs/experiment7_rightsizing.md and scripts/docker_benchmark.ps1
for the container-based variant that enforces --cpus/--memory.

Usage:  python scripts/benchmark.py [--cores 1,2,4,8] [--reps 3] [--scale 6]
"""
import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "experiments" / "results"


def worker(cores: int, scale: int) -> dict:
    import psutil
    proc = psutil.Process()
    if hasattr(proc, "cpu_affinity"):
        proc.cpu_affinity(list(range(cores)))
    sys.path.insert(0, str(ROOT))
    import pandas as pd
    from canesense import engine
    from canesense.data import add_features, label_urgency, simulate
    from canesense.model import predict, train

    t = {}
    t0 = time.perf_counter()
    frames = []
    for s in range(scale):
        plots, obs = simulate(1000 + s)
        frames.append(obs.assign(seed=s))
    obs = pd.concat(frames, ignore_index=True)
    t["simulate_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    df = add_features(obs)
    df["urgency"] = label_urgency(df)
    t["features_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    clf, metrics = train(df=df, n_estimators=300, n_jobs=cores)
    t["train_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    snap = df.drop(columns=["urgency", "stage_threshold", "soil_whc"])
    snap = snap[snap.date == snap.date.max()].copy()
    snap["area_ha"], snap["irrigation_type"], snap["sensor_status"] = 1.5, "Drip", "Online"
    snap["battery_pct"], snap["sensor_id"], snap["variety"] = 80, "SN", "Co 86032"
    pred = predict(clf, df.drop(columns=["urgency"]))
    t["inference_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    last = pred[pred.date == pred.date.max()].copy()
    last["area_ha"], last["irrigation_type"], last["sensor_status"] = 1.5, "Drip", "Online"
    last["battery_pct"], last["sensor_id"], last["variety"] = 80, "SN", "Co 86032"
    for _ in range(20):
        engine.recommend(last)
    t["recommend_s"] = time.perf_counter() - t0
    mi = proc.memory_info()
    peak = getattr(mi, "peak_wset", mi.rss)
    return dict(stages=t, total_s=sum(t.values()), peak_rss_mb=peak / 2**20, rows=int(len(df)), f1_macro=metrics["f1_macro"])


def run_profile(cores: int, reps: int, scale: int) -> dict:
    runs = []
    for i in range(reps):
        env = dict(os.environ, OMP_NUM_THREADS=str(cores), OPENBLAS_NUM_THREADS=str(cores), MKL_NUM_THREADS=str(cores), PYTHONHASHSEED="0")
        t0 = time.perf_counter()
        out = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--worker", str(cores), "--scale", str(scale)],
                             capture_output=True, text=True, env=env, cwd=str(ROOT))
        wall = time.perf_counter() - t0
        if out.returncode:
            raise RuntimeError(out.stderr[-800:])
        r = json.loads(out.stdout.strip().splitlines()[-1])
        r["wall_s"] = wall
        runs.append(r)
        print(f"  {cores} core(s) rep {i + 1}: workload {r['total_s']:.2f}s, process wall {wall:.2f}s, peak {r['peak_rss_mb']:.0f} MB", flush=True)
    med = statistics.median(r["total_s"] for r in runs)
    stages = {k: round(statistics.median(r["stages"][k] for r in runs), 3) for k in runs[0]["stages"]}
    return dict(profile=f"{cores} vCPU", cores=cores, reps=reps, median_s=round(med, 3), min_s=round(min(r["total_s"] for r in runs), 3),
                max_s=round(max(r["total_s"] for r in runs), 3), peak_rss_mb=round(max(r["peak_rss_mb"] for r in runs), 1), rows=runs[0]["rows"], stages=stages,
                f1_macro=round(runs[0]["f1_macro"], 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--cores", default="1,2,4,8")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--scale", type=int, default=6, help="number of 28-plot estates simulated (rows = scale x 4,200)")
    a = ap.parse_args()
    if a.worker:
        print(json.dumps(worker(a.worker, a.scale)))
        return
    import psutil
    cores = [int(c) for c in a.cores.split(",")]
    profiles = [run_profile(c, a.reps, a.scale) for c in cores]
    base = profiles[0]["median_s"]
    for p in profiles:
        p["speedup"] = round(base / p["median_s"], 2)
        p["efficiency_pct"] = round(100 * p["speedup"] / (p["cores"] / profiles[0]["cores"]), 1)
    mem = []
    for sc in (1, 3, a.scale):
        env = dict(os.environ, OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", PYTHONHASHSEED="0")
        out = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--worker", "2", "--scale", str(sc)], capture_output=True, text=True, env=env, cwd=str(ROOT))
        r = json.loads(out.stdout.strip().splitlines()[-1])
        mem.append(dict(scale=sc, rows=r["rows"], peak_rss_mb=round(r["peak_rss_mb"], 1), total_s=round(r["total_s"], 2)))
        print(f"  memory scaling x{sc}: {r['rows']:,} rows, peak {r['peak_rss_mb']:.0f} MB", flush=True)
    res = dict(
        experiment="Experiment 7 - Cloud resource right-sizing", generated=datetime.now().isoformat(timespec="seconds"),
        workload=f"CaneSense analytics pipeline: simulate {a.scale} synthetic estates ({profiles[0]['rows']:,} plot-day rows), label, train RandomForest (300 trees), "
                 f"batch inference on all rows, 20x recommendation-engine runs. Fixed seed.",
        host=f"{platform.system()} {platform.release()}, {platform.processor()}, {psutil.cpu_count(logical=True)} logical CPUs, {psutil.virtual_memory().total / 2**30:.0f} GiB RAM, Python {platform.python_version()}",
        method=f"Each profile = fresh subprocess pinned to N logical CPUs via OS affinity (+ BLAS/OpenMP thread caps), {a.reps} repetitions, median reported. Peak memory = max peak working set.",
        caveat="Local emulation: CPU count is enforced by affinity but memory is only measured, not capped, and the host CPU differs from any cloud instance. Treat as relative scaling evidence, "
               "not a prediction of absolute cloud timings. Container-enforced limits: scripts/docker_benchmark.ps1 (not executed - Docker unavailable on this machine).",
        profiles=profiles, memory_scaling=mem)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "rightsizing.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    import pandas as pd
    pd.DataFrame([{k: v for k, v in p.items() if k != "stages"} | {f"stage_{k}": v for k, v in p["stages"].items()} for p in profiles]).to_csv(RES / "rightsizing.csv", index=False)
    chart(profiles)
    print(json.dumps([{k: v for k, v in p.items() if k != "stages"} for p in profiles], indent=1))


def chart(profiles):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4), dpi=150)
    x = [p["profile"] for p in profiles]
    ax[0].bar(x, [p["median_s"] for p in profiles], color="#1D5A41")
    ax[0].set_title("Median workload time (s)", fontsize=10)
    ax[1].plot([p["cores"] for p in profiles], [p["speedup"] for p in profiles], "o-", color="#4FAE4B", label="Measured")
    ax[1].plot([p["cores"] for p in profiles], [p["cores"] / profiles[0]["cores"] for p in profiles], "--", color="#999", label="Ideal")
    ax[1].set_title("Speed-up vs 1 vCPU", fontsize=10); ax[1].legend(fontsize=8)
    ax[2].bar(x, [p["peak_rss_mb"] for p in profiles], color="#4B7CA6")
    ax[2].set_title("Peak memory (MB)", fontsize=10)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(RES / "rightsizing.png")


if __name__ == "__main__":
    main()
