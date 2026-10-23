import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def test_kubernetes_manifests_parse_and_have_probes_and_resources():
    docs = []
    for f in sorted((ROOT / "k8s").glob("*.yaml")):
        docs += [d for d in yaml.safe_load_all(f.read_text()) if d]
    kinds = {d["kind"] for d in docs}
    assert {"Namespace", "ConfigMap", "Deployment", "Service", "HorizontalPodAutoscaler"} <= kinds
    dep = next(d for d in docs if d["kind"] == "Deployment")
    c = dep["spec"]["template"]["spec"]["containers"][0]
    assert c["readinessProbe"]["httpGet"]["path"] == "/_stcore/health" and c["livenessProbe"]
    assert {"cpu", "memory"} <= set(c["resources"]["requests"]) and {"cpu", "memory"} <= set(c["resources"]["limits"])
    svc = next(d for d in docs if d["kind"] == "Service")
    assert svc["spec"]["selector"] == dep["spec"]["selector"]["matchLabels"]


def test_dockerfile_copies_assets_and_exposes_streamlit():
    t = (ROOT / "Dockerfile").read_text()
    for needle in ("COPY assets", "COPY canesense", "COPY views", "EXPOSE 8501", "HEALTHCHECK", "USER 10001", "train_model.py"):
        assert needle in t
    assert "scratch/" in (ROOT / ".dockerignore").read_text()


def test_local_assets_and_credits_exist():
    for f in ("hero_sugarcane_1500.jpg", "field_header.jpg", "irrigation_header.jpg", "soil_sensor.jpg"):
        assert (ROOT / "assets" / "images" / f).stat().st_size > 5_000
    credits = (ROOT / "assets" / "IMAGE_CREDITS.md").read_text(encoding="utf-8")
    for f in ("hero_sugarcane.jpg", "field_tamilnadu.jpg", "irrigation_nrcs.jpg", "soil_sensor.jpg"):
        assert f in credits
    assert (ROOT / "assets" / "brand" / "favicon.png").exists()


def test_no_secrets_in_source():
    pat = re.compile(r"(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}", re.I)
    for f in list(ROOT.glob("canesense/*.py")) + list(ROOT.glob("views/*.py")) + [ROOT / "app.py"]:
        assert not pat.search(f.read_text(encoding="utf-8")), f
