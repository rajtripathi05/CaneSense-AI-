from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from canesense import charts, engine, state, ui
from canesense.config import REFERENCE_DATE
from canesense.data import IRRIGATION

ss = st.session_state
ss.setdefault("ops_log", [])
df = state.frame()
ui.shell("Irrigation Operations", "Priority queue, suggested pump schedule and simulated action management")
ui.band("irrigation", "Suggestions only - no pumps or real equipment are controlled")

queue = df[df.volume_m3 > 0].sort_values("rank").copy()
k = engine.kpis(df)
used, budget = df.attrs.get("used_m3", df.allocated_m3.sum()), df.attrs.get("budget_m3", 0)
c = st.columns(4)
c[0].markdown(ui.kpi("Actions queued", str(len(queue)), "plots", f"{int((queue.action == engine.A_IRRIGATE).sum())} irrigate soon", "droplet", "amber"), unsafe_allow_html=True)
c[1].markdown(ui.kpi("Allocated today", f"{k['allocated_m3']:,.0f}", "m³", f"of {df.attrs.get('budget_m3', 0):,.0f} m³ budget", "rain", "blue"), unsafe_allow_html=True)
c[2].markdown(ui.kpi("Deferred", str(k["restricted"]), "plots", "no water budget left", "alert", "red" if k["restricted"] else "green"), unsafe_allow_html=True)
done = sum(1 for v in ss.ops_status.values() if v == "Completed")
c[3].markdown(ui.kpi("Completed (simulated)", str(done), "plots", "moisture updated in the model", "check", "green"), unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Priority queue", "Suggested pump schedule", "Action log"])
with tab1:
    if queue.empty:
        ui.empty("No irrigation actions queued", "Current conditions do not require irrigation. Try the Dry Spell scenario to see the queue fill up.")
    else:
        view = pd.DataFrame({"Rank": queue["rank"].astype(int), "Plot": queue.plot_id, "Village": queue.village, "Urgency": queue.urgency,
                             "Action": queue.action, "Water (m³)": queue.volume_m3, "Allocated (m³)": queue.allocated_m3, "Duration (h)": queue.duration_h,
                             "System": queue.irrigation_type,
                             "Status": [ss.ops_status.get(p, "Pending") for p in queue.plot_id]})
        edited = st.data_editor(view, hide_index=True, width="stretch", key="ops_editor", disabled=[c for c in view.columns if c != "Status"],
                                column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Pending", "Scheduled", "Completed", "Deferred"], required=True),
                                               "Water (m³)": st.column_config.NumberColumn(format="%d"), "Allocated (m³)": st.column_config.NumberColumn(format="%d"),
                                               "Duration (h)": st.column_config.NumberColumn(format="%.1f")})
        changed = edited[edited.Status != view.Status]
        if st.button("Apply status changes", type="primary", icon=":material/done_all:", disabled=changed.empty,
                     help="Change at least one Status cell first." if changed.empty else "Saves statuses; completed plots receive simulated irrigation."):
            for _, r in changed.iterrows():
                src = queue[queue.plot_id == r.Plot].iloc[0]
                ss.ops_status[r.Plot] = r.Status
                if r.Status == "Completed":
                    ss.overrides[r.Plot] = round(src.depth_mm * IRRIGATION[src.irrigation_type][0], 1)
                else:
                    ss.overrides.pop(r.Plot, None)
                ss.ops_log.append(dict(Time=datetime.now().strftime("%H:%M:%S"), Plot=r.Plot, Status=r.Status, Action=src.action))
            ss.flash = f"{len(changed)} status change(s) saved"
            st.rerun()
        if ss.get("flash"):
            st.toast(ss.pop("flash"), icon=":material/check_circle:")
with tab2:
    plan = queue[(queue.allocated_m3 > 0) & (queue.plot_id.map(lambda p: ss.ops_status.get(p, "Pending")).isin(["Pending", "Scheduled"]))]
    if plan.empty:
        ui.empty("Nothing to schedule", "No plots have allocated water and an open status.")
    else:
        t0 = datetime.fromisoformat(REFERENCE_DATE) + timedelta(days=1, hours=5, minutes=30)
        free = {f"Pump {n}": t0 for n in "ABC"}
        rows = []
        for _, r in plan.iterrows():
            p = min(free, key=free.get)
            s, e = free[p], free[p] + timedelta(hours=float(r.duration_h))
            free[p] = e + timedelta(minutes=15)
            rows.append(dict(pump=p, plot_id=r.plot_id, urgency=r.urgency, start=s, end=e, duration_h=r.duration_h, volume_m3=r.allocated_m3))
        sch = pd.DataFrame(rows)
        st.plotly_chart(charts.schedule(sch), width="stretch", config={"displayModeBar": False}, key="ops_gantt")
        st.caption("Greedy plan: highest-priority plots first, assigned to the pump that frees up earliest (15 min changeover). Simulated, 3 pumps, start 05:30.")
        out = sch.assign(Start=sch.start.dt.strftime("%d %b %H:%M"), End=sch.end.dt.strftime("%d %b %H:%M"))[["pump", "plot_id", "Start", "End", "duration_h", "volume_m3"]]
        out.columns = ["Pump", "Plot", "Start", "End", "Hours", "Water (m³)"]
        st.dataframe(out, hide_index=True, width="stretch")
with tab3:
    if ss.ops_log:
        st.dataframe(pd.DataFrame(ss.ops_log[::-1]), hide_index=True, width="stretch")
    else:
        ui.empty("No actions logged", "Status changes made in the Priority queue are logged here.")
