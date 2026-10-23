import time

import pandas as pd
import streamlit as st

from canesense import charts, scenarios, service, state, ui

ss = st.session_state
if ss.get("flash"):
    st.toast(ss.pop("flash"), icon=":material/check_circle:")

df = state.frame()
ui.shell("Scenario Simulator", "Pick a deterministic scenario, preview the impact, then apply it to the whole dashboard")

names = list(scenarios.SCENARIOS)
ui.section("1 · Choose a scenario", "Presets are deterministic - the same scenario always gives the same result")
for chunk in (names[:4], names[4:]):
    cols = st.columns(4)
    for col, name in zip(cols, chunk):
        s = scenarios.SCENARIOS[name]
        cls = "active" if name == ss.scenario else ("preview" if name == ss.preview else "")
        tag = ui.chip("Active", "ok", "check") if name == ss.scenario else (ui.chip("Previewing", "info") if name == ss.preview else "")
        with col:
            ui.md(f'<div class="cs-card cs-scn {cls}"><div style="display:flex;justify-content:space-between;gap:.4rem"><span class="nm">{name}</span>{tag}</div>'
                  f'<div class="bl">{s["blurb"]}</div></div>')
            if st.button("Preview impact", key=f"pv_{name}", icon=s["icon"], width="stretch"):
                ss.preview = name
                st.rerun()

before = service.summary(df)
ui.section("2 · Preview and apply")
target = ss.preview
if not target:
    ui.empty("No scenario selected", "Choose a scenario above to see how it would change risk, water demand and sensor health before you apply it.")
else:
    s = scenarios.SCENARIOS[target]
    after_df = state.frame_for(target)
    after = service.summary(after_df)

    def cell(label, b, a, fmt="{:,.0f}", bad_up=True):
        d = a - b
        cls = "same" if abs(d) < 0.5 else ("bad" if (d > 0) == bad_up else "good")
        arrow = "" if cls == "same" else f"{'▲' if d > 0 else '▼'} {abs(d):,.0f}"
        return f"<div><span>{label}</span><b>{fmt.format(b)} → {fmt.format(a)}</b><em class='{cls}'>{arrow}</em></div>"

    ui.md(f'<div class="cs-card"><h4>{target}</h4><p style="margin:.1rem 0 .7rem">{s["change"]}</p><div class="cs-delta">'
          + cell("High-urgency plots", before["high_risk"], after["high_risk"]) + cell("Need irrigation", before["need_irrigation"], after["need_irrigation"])
          + cell("Water demand (m³)", before["demand_m3"], after["demand_m3"]) + cell("Deferred by budget", before["restricted"], after["restricted"])
          + cell("Rain adjustments", before["rain_adjust"], after["rain_adjust"], bad_up=False)
          + cell("Sensors offline", before["sensors_offline"], after["sensors_offline"]) + "</div></div>")
    same = target == ss.scenario and not ss.overrides
    a1, a2, a3 = st.columns([1.2, 1.4, 3])
    go = a1.button("Apply Scenario", type="primary", icon=":material/play_arrow:", width="stretch", disabled=same,
                   help="This scenario is already active." if same else "Updates readings, predictions, charts, map and alerts everywhere.")
    rs = a2.button("Reset to Normal", icon=":material/restart_alt:", width="stretch", disabled=(ss.scenario == scenarios.NORMAL and not ss.overrides),
                   help="Already on Normal Conditions." if ss.scenario == scenarios.NORMAL and not ss.overrides else "Restore baseline readings and clear simulated actions.")
    if go or rs:
        name = scenarios.NORMAL if rs else target
        with st.status(f"Applying “{name}”…", expanded=True) as status:
            for step in ("Updating synthetic sensor readings", "Re-running the ML model on every plot", "Recomputing recommendations and water budget",
                         "Refreshing dashboard, map and alerts"):
                st.write(f"• {step}")
                time.sleep(0.35)
            ch = state.apply_scenario(name)
            status.update(label=f"Scenario applied: {name}", state="complete", expanded=False)
        ss.flash = f"{name} applied · high-urgency plots {ch['before']['high_risk']} → {ch['after']['high_risk']}"
        st.rerun()

ch = ss.last_change
ui.section("3 · What changed")
if not ch:
    ui.empty("Nothing applied yet", "After you apply a scenario, a before/after summary and a timestamped event appear here.")
else:
    b, a = ch["before"], ch["after"]
    l, r = st.columns([2, 3])
    with l:
        st.plotly_chart(charts.before_after(b, a), width="stretch", config={"displayModeBar": False}, key="sim_ba")
        st.caption("Plots at each urgency level before and after the last applied scenario.")
    with r:
        st.success(f"**{ch['scenario']}** applied at {ch['time']}.", icon=":material/check_circle:")
        tbl = pd.DataFrame({"Metric": ["High-urgency plots", "Medium", "Need irrigation", "Water demand (m³)", "Deferred by budget", "Sensor review needed"],
                            "Before": [b["high_risk"], b["medium_risk"], b["need_irrigation"], round(b["demand_m3"]), b["restricted"], b["review"]],
                            "After": [a["high_risk"], a["medium_risk"], a["need_irrigation"], round(a["demand_m3"]), a["restricted"], a["review"]]})
        tbl["Change"] = tbl.After - tbl.Before
        st.dataframe(tbl, hide_index=True, width="stretch")
        top = df.sort_values("rank").head(3)
        st.markdown("**Now highest priority:** " + ", ".join(f"{r.plot_id} ({r.action})" for _, r in top.iterrows()))

ui.section("Scenario history")
if ss.history:
    st.dataframe(pd.DataFrame(ss.history[::-1]), hide_index=True, width="stretch")
else:
    ui.empty("No scenario events yet", "Applied scenarios are logged here with a timestamp.")
