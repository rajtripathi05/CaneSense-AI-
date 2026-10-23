# CaneSense AI - Experiment 2. Build: docker build -t canesense-ai:1.0 .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Same asset structure as local development: assets/images, assets/brand, models, experiments/results
COPY app.py ./
COPY .streamlit ./.streamlit
COPY canesense ./canesense
COPY views ./views
COPY scripts ./scripts
COPY assets ./assets
COPY experiments ./experiments
COPY evidence ./evidence
COPY data ./data
COPY docs ./docs

# Train the model inside the image so the pickle always matches the image's scikit-learn version.
RUN mkdir -p models && python scripts/train_model.py \
 && useradd --create-home --uid 10001 cane && chown -R cane:cane /app
USER 10001

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4).status==200 else 1)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
