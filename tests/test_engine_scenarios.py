import pytest

from canesense import engine, scenarios, service


def k(name):
    return service.summary(service.scenario_frame(name))


def test_scenarios_are_deterministic():
    a = service.scenario_frame("Simulate Dry Spell")
    b = service.scenario_frame("Simulate Dry Spell")
    assert a.equals(b)


def test_dry_spell_increases_risk_and_demand():
    n, d = k(scenarios.NORMAL), k("Simulate Dry Spell")
    assert d["high_risk"] > n["high_risk"] and d["demand_m3"] > n["demand_m3"]


def test_rain_expected_shifts_advice_to_rain_adjustment():
    n, r = k(scenarios.NORMAL), k("Rain Expected")
    assert r["rain_adjust"] > n["rain_adjust"] and r["demand_m3"] < n["demand_m3"]


def test_sensor_failure_flags_review():
    s = service.scenario_frame("Sensor Failure")
    assert (s.sensor_status == "Offline").sum() == 7
    off = s[s.sensor_status == "Offline"]
    assert (off.action == engine.A_SENSOR).all() and off.volume_m3.eq(0).all()


def test_water_restriction_defers_plots_within_budget():
    r = service.scenario_frame("Water Availability Restricted")
    assert r.attrs["used_m3"] <= r.attrs["budget_m3"] + 1e-6
    assert (r.action == engine.A_RESTRICT).sum() > 0
    assert r[r.action == engine.A_RESTRICT].allocated_m3.eq(0).all()


def test_reco_quantities_are_consistent():
    d = service.scenario_frame(scenarios.NORMAL)
    act = d[d.action == engine.A_IRRIGATE]
    assert (act.volume_m3 > 0).all() and (act.duration_h > 0).all()
    assert (d[d.action == engine.A_MONITOR].volume_m3 == 0).all()


def test_overrides_simulate_completed_irrigation():
    before = service.scenario_frame("Simulate Dry Spell")
    pid = before.sort_values("rank").plot_id.iloc[0]
    after = service.scenario_frame("Simulate Dry Spell", ((pid, 40.0),))
    assert after.set_index("plot_id").loc[pid, "soil_moisture"] > before.set_index("plot_id").loc[pid, "soil_moisture"]


def test_unknown_scenario_raises():
    with pytest.raises(ValueError):
        scenarios.apply(service.baseline()["current"], "Nope")
