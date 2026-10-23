import numpy as np
import pandas as pd

from canesense import data, model, service


def test_dataset_is_reproducible_and_large_enough():
    a, oa = data.simulate(42)
    b, ob = data.simulate(42)
    assert len(a) >= 24 and a.plot_id.is_unique
    pd.testing.assert_frame_equal(oa, ob)
    assert len(oa) == len(a) * data.SIM_DAYS
    assert a.village.nunique() == 6


def test_different_seed_changes_data():
    _, o1 = data.simulate(1, 30)
    _, o2 = data.simulate(2, 30)
    assert not o1.soil_moisture.equals(o2.soil_moisture)


def test_validation_accepts_baseline_and_rejects_bad_input():
    cur = service.baseline()["current"]
    assert data.validate_frame(cur) == []
    bad = cur.copy()
    bad.loc[0, "humidity"] = 180
    bad.loc[1, "crop_stage"] = "Nonsense"
    msgs = data.validate_frame(bad)
    assert any("humidity" in m for m in msgs) and any("crop stage" in m.lower() for m in msgs)
    assert "Missing required column" in data.validate_frame(cur.drop(columns=["et0"]))[0]


def test_model_split_metrics_and_inference():
    clf, m = model.train(n_estimators=60)
    assert m["n_train"] + m["n_test"] == data.SIM_DAYS * 28
    assert abs(m["n_test"] / (m["n_train"] + m["n_test"]) - 0.25) < 0.01
    for k in ("accuracy", "precision_macro", "recall_macro", "f1_macro"):
        assert 0.6 < m[k] <= 1.0
    cur = service.baseline()["current"]
    p = model.predict(clf, cur)
    assert set(p.urgency) <= {"Low", "Medium", "High"}
    assert np.allclose(p[["p_low", "p_medium", "p_high"]].sum(axis=1), 1.0)


def test_predict_handles_missing_sensor_value():
    clf, _ = service.model_bundle()
    cur = service.baseline()["current"].copy()
    cur.loc[3, "soil_moisture"] = np.nan
    p = model.predict(clf, cur)
    assert p.loc[3, "imputed"] and not p.loc[2, "imputed"]
    assert p.urgency.notna().all()
