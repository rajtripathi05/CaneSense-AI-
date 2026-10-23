"""scikit-learn irrigation-urgency classifier: train / evaluate / load / predict."""
from __future__ import annotations
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.model_selection import train_test_split, cross_val_score

from .config import MODEL_DIR, SEED
from .data import FEATURES, add_features, label_urgency, simulate

CLASSES = ["Low", "Medium", "High"]
MODEL_PATH = MODEL_DIR / "urgency_rf.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"


def training_frame(seed: int = SEED, n_days: int = 150) -> pd.DataFrame:
    _, obs = simulate(seed, n_days)
    df = add_features(obs)
    df["urgency"] = label_urgency(df)
    return df


def train(seed: int = SEED, n_estimators: int = 300, n_jobs: int = 1, df: pd.DataFrame | None = None):
    """Train with a stratified 75/25 split. Returns (model, metrics dict). Labels are synthetic."""
    df = training_frame(seed) if df is None else df
    X, y = df[FEATURES], df["urgency"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
    clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=12, min_samples_leaf=2,
                                 class_weight="balanced", random_state=seed, n_jobs=n_jobs)
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    p, r, f, _ = precision_recall_fscore_support(yte, pred, labels=CLASSES, average="macro", zero_division=0)
    pc, rc, fc, sc = precision_recall_fscore_support(yte, pred, labels=CLASSES, zero_division=0)
    cv = cross_val_score(RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_leaf=2,
                         class_weight="balanced", random_state=seed, n_jobs=n_jobs), X, y, cv=5, scoring="f1_macro")
    metrics = dict(
        n_train=int(len(Xtr)), n_test=int(len(Xte)), split="stratified 75/25", seed=seed,
        accuracy=float(accuracy_score(yte, pred)), precision_macro=float(p), recall_macro=float(r), f1_macro=float(f),
        cv_f1_macro_mean=float(cv.mean()), cv_f1_macro_std=float(cv.std()),
        per_class={c: dict(precision=float(pc[i]), recall=float(rc[i]), f1=float(fc[i]), support=int(sc[i])) for i, c in enumerate(CLASSES)},
        confusion_matrix=confusion_matrix(yte, pred, labels=CLASSES).tolist(), classes=CLASSES,
        feature_importance=dict(sorted(zip(FEATURES, map(float, clf.feature_importances_)), key=lambda t: -t[1])),
        note="Labels come from a synthetic agronomic rule plus noise. Metrics show how well the model recovers that "
             "synthetic rule; they are NOT evidence of accuracy on real sugarcane farms.",
    )
    return clf, metrics


def load_or_train():
    """Load the persisted model, training (and saving) it first if absent."""
    if MODEL_PATH.exists() and METRICS_PATH.exists():
        try:
            return joblib.load(MODEL_PATH), json.loads(METRICS_PATH.read_text())
        except Exception:
            pass
    clf, metrics = train()
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(clf, MODEL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return clf, metrics


def predict(clf, df: pd.DataFrame) -> pd.DataFrame:
    """Add predicted urgency + class probabilities. Missing sensor values are imputed from the village median
    and flagged via `imputed`."""
    out = add_features(df)
    X = out[FEATURES].copy()
    imputed = X["soil_moisture"].isna()
    if imputed.any():
        med = out.groupby("village")["soil_moisture"].transform("median").fillna(out["soil_moisture"].median())
        X.loc[imputed, "soil_moisture"] = med[imputed]
    proba = clf.predict_proba(X)
    idx = {c: list(clf.classes_).index(c) for c in CLASSES}
    out["p_low"], out["p_medium"], out["p_high"] = (proba[:, idx[c]] for c in CLASSES)
    out["urgency"] = clf.classes_[proba.argmax(axis=1)]
    out["confidence"] = proba.max(axis=1)
    out["imputed"] = imputed
    return out
