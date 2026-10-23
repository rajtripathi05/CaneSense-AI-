import json
import urllib.request

import pandas as pd
import streamlit as st

from canesense import charts, ui
from canesense.config import CLOUD_ENDPOINT, EVIDENCE, EXPERIMENTS, ROOT
from canesense.theme import C

ui.shell("Cloud Lab", "Docker, Kubernetes, right-sizing and FinOps experiments - with honest verification status")


def status(folder: str) -> dict:
    p = EVIDENCE / folder / "status.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "unknown", "summary": "No status file found.", "next": ""}


def load(name: str):
    p = EXPERIMENTS / "results" / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


KIND = {"executed": ("ok", "Executed - results on file"), "partial": ("warn", "Partly verified"), "not_executed": ("warn", "Not executed on this machine"), "unknown": ("neutral", "Unknown")}
EXPS = [("exp2_docker", "Experiment 2 · Docker & Docker Hub"), ("exp3_kubernetes", "Experiment 3 · Kubernetes"),
        ("exp7_rightsizing", "Experiment 7 · Right-sizing"), ("exp8_finops", "Experiment 8 · FinOps")]
cols = st.columns(4)
for col, (f, title) in zip(cols, EXPS):
    s = status(f)
    k, lab = KIND.get(s["status"], KIND["unknown"])
    col.markdown(f"<div class='cs-card' style='min-height:130px'><h4>{title}</h4>{ui.chip(lab, k)}<p style='font-size:.8rem;margin:.5rem 0 0'>{s['summary']}</p></div>", unsafe_allow_html=True)

tabs = st.tabs(["Docker", "Kubernetes", "Right-sizing", "FinOps", "Cloud connection"])
with tabs[0]:
    s = status("exp2_docker")
    st.markdown(f"**Status:** {s['summary']}")
    st.code("docker build -t canesense-ai:1.0 .\ndocker run -d -p 8501:8501 --name canesense canesense-ai:1.0\n"
            "curl http://localhost:8501/_stcore/health\n\n# Docker Hub (replace <user>)\ndocker login\ndocker tag canesense-ai:1.0 <user>/canesense-ai:1.0\n"
            "docker push <user>/canesense-ai:1.0", language="bash")
    if s.get("next"):
        st.info(s["next"])
    st.caption("Full guide: docs/experiment2_docker.md")
with tabs[1]:
    s = status("exp3_kubernetes")
    st.markdown(f"**Status:** {s['summary']}")
    st.code("kubectl apply -f k8s/\nkubectl -n canesense get pods,svc\nkubectl -n canesense scale deployment/canesense-ai --replicas=3\n"
            "kubectl -n canesense delete pod -l app=canesense-ai   # self-healing check\nkubectl -n canesense port-forward svc/canesense-ai 8501:80", language="bash")
    if s.get("next"):
        st.info(s["next"])
    st.caption("Full guide: docs/experiment3_kubernetes.md · manifests in k8s/")
with tabs[2]:
    rs = load("rightsizing.json")
    if not rs:
        ui.empty("No benchmark results yet", "Run `python scripts/benchmark.py` to measure the analytics workload at several CPU settings.")
    else:
        d = pd.DataFrame(rs["profiles"])
        d = pd.concat([d.drop(columns=["stages"]), pd.DataFrame(list(d["stages"])).add_prefix("stage_")], axis=1)
        st.markdown(f"**Workload:** {rs['workload']}  \n**Host:** {rs['host']}  \n**Method:** {rs['method']}")
        a, b = st.columns(2)
        a.plotly_chart(charts.bar_compare(d.profile, d.median_s, "Median runtime (s) - lower is better", "seconds", text=d.median_s.round(2)), width="stretch", key="rs_t", config={"displayModeBar": False})
        b.plotly_chart(charts.bar_compare(d.profile, d.peak_rss_mb, "Peak memory (MB RSS)", "MB", color=C["blue"], text=d.peak_rss_mb.round(0)), width="stretch", key="rs_m", config={"displayModeBar": False})
        st.dataframe(d, hide_index=True, width="stretch")
        if rs.get("memory_scaling"):
            st.markdown("**Memory vs data volume (2 vCPU)**")
            st.dataframe(pd.DataFrame(rs["memory_scaling"]), hide_index=True, width="stretch")
        st.caption(rs["caveat"])
with tabs[3]:
    fo = load("finops.json")
    if not fo:
        ui.empty("No FinOps results yet", "Run `python scripts/finops.py` after the benchmark.")
    else:
        d = pd.DataFrame(fo["instances"])
        st.warning(fo["assumptions"], icon=":material/info:")
        a, b = st.columns(2)
        a.plotly_chart(charts.bar_compare(d.instance, d.monthly_always_on_usd, "Estimated monthly cost, always on (USD)", "USD / month", text=d.monthly_always_on_usd.round(1)), width="stretch", key="fo_m", config={"displayModeBar": False})
        b.plotly_chart(charts.bar_compare(d.instance, d.cost_per_1000_runs_usd, "Estimated cost per 1,000 workload runs (USD)", "USD", color=C["amber"], text=d.cost_per_1000_runs_usd.round(3)), width="stretch", key="fo_r", config={"displayModeBar": False})
        st.dataframe(d, hide_index=True, width="stretch")
        st.caption(fo["disclaimer"])
with tabs[4]:
    if not CLOUD_ENDPOINT:
        ui.empty("Cloud service not configured", "Set the environment variable CANESENSE_CLOUD_URL to an HTTP health endpoint to enable a live connection check. "
                 "The app works fully offline without it.")
    else:
        st.write(f"Configured endpoint: `{CLOUD_ENDPOINT}`")
        if st.button("Check connection now", icon=":material/cloud_sync:"):
            try:
                with urllib.request.urlopen(CLOUD_ENDPOINT, timeout=4) as r:
                    st.success(f"Reachable: HTTP {r.status}")
            except Exception as e:
                st.error(f"Not reachable ({type(e).__name__}). The dashboard is unaffected.")
