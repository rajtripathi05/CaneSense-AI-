# Deploy CaneSense AI on Streamlit Community Cloud

1. Open https://share.streamlit.io/ → sign in with GitHub (rajtripathi05) → **Create app** → "Deploy a public app from GitHub".
2. Repository: `rajtripathi05/CaneSense-AI-` (https://github.com/rajtripathi05/CaneSense-AI-, public)
3. Branch: `main`
4. Main file path: `app.py`
5. App URL (Advanced settings → subdomain): `canesense-ai-raj` (if taken, pick another)
6. Advanced settings → Python version: `3.12`
7. Secrets: none required (synthetic data, no API keys).
8. Click **Deploy**.

Dependencies: root `requirements.txt` (streamlit, pandas, numpy, scikit-learn, joblib, plotly, reportlab, xlsxwriter, openpyxl, matplotlib, psutil, pyyaml).
