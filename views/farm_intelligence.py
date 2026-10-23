import streamlit as st

from canesense import engine, panels, state, ui
from canesense.data import STAGES
from canesense.theme import RISK_ICON

df, hist = state.frame(), state.history()
ui.shell("Farm Intelligence", "Operational data workspace · search, filter, and open any plot")
ui.band("field", "Plot-level sensor readings, urgency and recommended actions")

K = panels.FILTER_KEYS
c1, c2, c3, c4, c5 = st.columns([2, 1.4, 1.4, 1.4, 1.4])
q = c1.text_input("Search plot or village", key=K["q"], placeholder="e.g. CS-P07 or Chandanpur")
risk = c2.multiselect("Urgency", ["High", "Medium", "Low"], key=K["risk"], placeholder="All")
stage = c3.multiselect("Crop stage", STAGES, key=K["stage"], placeholder="All")
sensor = c4.multiselect("Sensor status", ["Online", "Degraded", "Offline"], key=K["sensor"], placeholder="All")
village = c5.multiselect("Village", sorted(df.village.unique()), key=K["village"], placeholder="All")
f = panels.apply_filters(df, q, risk, stage, sensor, village).sort_values("rank")

b1, b2, b3 = st.columns([3, 1, 1])
with b1:
    ui.md(f"{ui.chip('Scenario: ' + st.session_state.scenario, 'neutral' if st.session_state.scenario == 'Normal Conditions' else 'warn', 'activity')} "
          f"{ui.chip(f'{len(f)} of {len(df)} plots', 'info', 'layers')}")
b2.button("Reset filters", on_click=panels.reset_filters, icon=":material/restart_alt:", width="stretch",
          disabled=not any([q, risk, stage, sensor, village]), help=None if any([q, risk, stage, sensor, village]) else "No filters are active.")
if len(f):
    b3.download_button("Export CSV", f.sort_values("rank")[["plot_id", "village", "crop_stage", "soil_moisture", "urgency", "action", "volume_m3", "duration_h", "sensor_status"]]
                       .to_csv(index=False).encode(), file_name="canesense_filtered_plots.csv", mime="text/csv", icon=":material/download:", width="stretch")
else:
    b3.button("Export CSV", disabled=True, help="No records match the current filters.", width="stretch", icon=":material/download:")

if f.empty:
    ui.empty("No plots match these filters", "Try removing a filter or use Reset filters to see all plots again.")
    st.stop()

view = f.copy()
view["risk"] = view.urgency.map(lambda u: f"{RISK_ICON[u]} {u}")
cols = ["plot_id", "village", "crop_stage", "area_ha", "soil_moisture", "humidity", "et0", "risk", "action", "volume_m3", "sensor_status"]
colour = {"▲ High": "background-color:#F9E3DF;color:#8E241A;font-weight:600", "◆ Medium": "background-color:#FBF1D8;color:#7A5600;font-weight:600",
          "● Low": "background-color:#E8F4E3;color:#1F5E24;font-weight:600"}
styled = view[cols].style.map(lambda v: colour.get(v, ""), subset=["risk"]).map(
    lambda v: "color:#8E241A;font-weight:600" if v == "Offline" else ("color:#7A5600" if v == "Degraded" else ""), subset=["sensor_status"])
cfg = {
    "plot_id": st.column_config.TextColumn("Plot", width="small"), "village": "Village", "crop_stage": "Crop stage",
    "area_ha": st.column_config.NumberColumn("Area (ha)", format="%.1f"), "soil_moisture": st.column_config.NumberColumn("Moisture (%)", format="%.1f"),
    "soil_temp": st.column_config.NumberColumn("Soil temp (°C)", format="%.1f"), "air_temp": st.column_config.NumberColumn("Air temp (°C)", format="%.1f"),
    "humidity": st.column_config.NumberColumn("Humidity (%)", format="%.0f"), "et0": st.column_config.NumberColumn("ET0 (mm/d)", format="%.1f"),
    "risk": st.column_config.TextColumn("Urgency", width="small"), "action": st.column_config.TextColumn("Recommended action", width="medium"),
    "volume_m3": st.column_config.NumberColumn("Water (m³)", format="%d"), "sensor_status": st.column_config.TextColumn("Sensor", width="small"),
}
ev = st.dataframe(styled, column_config=cfg, hide_index=True, width="stretch", height=min(430, 38 + 35 * len(view)),
                  on_select="rerun", selection_mode="single-row", key="fi_table")
rows = ev.selection.rows if ev and ev.selection else []
if rows:
    pid = view.iloc[rows[0]].plot_id
    if pid != st.session_state.get("fi_last"):
        st.session_state.fi_last = pid
        state.select_plot(pid)

opts = list(view.plot_id)
ss = st.session_state
if ss.selected_plot in opts and ss.get("fi_last_pick") != ss.selected_plot:
    ss.fi_pick = ss.selected_plot            # selection made by clicking a table row or elsewhere
elif ss.get("fi_pick") not in opts:
    ss.fi_pick = None
pick = st.selectbox("Or choose a plot to inspect", opts, key="fi_pick", index=None, placeholder="Select a plot…")
if pick:
    state.select_plot(pick)
    ss.fi_last_pick = pick

sel = ui.selected_row(f)
ui.section("Plot detail")
if sel is None:
    ui.empty("No plot selected", "Click a row in the table (or choose a plot above) to see sensor readings, history, AI prediction and the recommended action.")
else:
    panels.plot_detail(sel, hist, key="fi")
