"""CaneSense AI - Precision Irrigation Intelligence (Streamlit entry point).

Run:  python -m streamlit run app.py
"""
import streamlit as st

from canesense import state, theme
from canesense.config import BRAND, APP_NAME, DESCRIPTOR

st.set_page_config(page_title=f"{APP_NAME} · {DESCRIPTOR}", page_icon=str(BRAND / "favicon.png"), layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"About": f"{APP_NAME} - synthetic-data demo of AI-assisted irrigation planning for sugarcane."})
st.markdown(theme.css(), unsafe_allow_html=True)
try:
    st.logo(str(BRAND / "logo_wordmark.svg"), icon_image=str(BRAND / "logo_mark.svg"))
except Exception:      # logo is cosmetic; never block the app
    pass
state.init()

PAGES = [
    st.Page("views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("views/farm_intelligence.py", title="Farm Intelligence", icon=":material/table_chart:", url_path="farm-intelligence"),
    st.Page("views/farm_map.py", title="Farm Map", icon=":material/map:", url_path="farm-map"),
    st.Page("views/advisor.py", title="AI Irrigation Advisor", icon=":material/psychology:", url_path="advisor"),
    st.Page("views/simulator.py", title="Scenario Simulator", icon=":material/science:", url_path="scenario-simulator"),
    st.Page("views/operations.py", title="Irrigation Operations", icon=":material/water_pump:", url_path="operations"),
    st.Page("views/reports.py", title="Reports & Exports", icon=":material/description:", url_path="reports"),
    st.Page("views/cloud_lab.py", title="Cloud Lab", icon=":material/cloud:", url_path="cloud-lab"),
    st.Page("views/methodology.py", title="Methodology", icon=":material/menu_book:", url_path="methodology"),
]
st.session_state["_pages"] = {p.title: p for p in PAGES}
pg = st.navigation(PAGES)

with st.sidebar:
    st.markdown(f"""<div class="cs-side-foot"><b>Demo Farm Cooperative</b><br>Operations team · demo user<br>
    <span style="opacity:.85">Scenario: {st.session_state.scenario}</span><br>
    <span style="opacity:.85">Synthetic data · no real farms</span></div>""", unsafe_allow_html=True)

try:
    pg.run()
except Exception as exc:  # last-resort guard: friendly message instead of a raw traceback
    st.error("Something went wrong while rendering this page. Please try again or reset the demo from the Scenario Simulator.")
    with st.expander("Technical detail"):
        st.code(f"{type(exc).__name__}: {exc}")
