import streamlit as st

from canesense import panels, state, ui

df, hist = state.frame(), state.history()
ui.shell("Farm Map", "Synthetic field-zone view · hover for details, click a plot to select it")

c1, c2, c3, c4 = st.columns([1.6, 1.4, 1.4, 1.8])
village = c1.multiselect("Village", sorted(df.village.unique()), key="fm_village", placeholder="All")
risk = c2.multiselect("Urgency", ["High", "Medium", "Low"], key="fm_risk", placeholder="All")
sensor = c3.multiselect("Sensor status", ["Online", "Degraded", "Offline"], key="fm_sensor", placeholder="All")
base = c4.radio("Base map", ["Field-zone (offline)", "Street tiles (needs internet)"], key="fm_base", horizontal=False)
f = panels.apply_filters(df, village=village, risk=risk, sensor=sensor)

if f.empty:
    ui.empty("No plots match these filters", "Clear a filter to bring plots back onto the map.")
    st.stop()

left, right = st.columns([3, 2])
with left:
    panels.map_chart(f, "fm_map", tiles=base.startswith("Street"))
    ui.legend()
    if base.startswith("Street"):
        st.caption("Street tiles load from OpenStreetMap and need an internet connection. If the tiles stay blank, switch back to the offline field-zone view. "
                   "Plot positions are synthetic and do not represent real farms.")
    else:
        st.caption("Offline field-zone view: village blocks and the canal are illustrative; plot coordinates are synthetic.")
with right:
    sel = ui.selected_row(f)
    if sel is None:
        ui.empty("Select a plot", "Click any marker to see its moisture, urgency and recommended action here.")
    else:
        ui.md(ui.reco_card(sel))
        if st.button("Open in AI Irrigation Advisor", icon=":material/psychology:", key="fm_goto"):
            st.switch_page(st.session_state["_pages"]["AI Irrigation Advisor"])

sel = ui.selected_row(f)
if sel is not None:
    ui.section("Plot detail", f"{sel.plot_id} · {sel.village}")
    panels.plot_detail(sel, hist, key="fm")
