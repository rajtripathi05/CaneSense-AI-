"""Train the urgency classifier and write models/urgency_rf.joblib + models/metrics.json."""
import json
import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from canesense.model import MODEL_DIR, MODEL_PATH, METRICS_PATH, train  # noqa: E402

if __name__ == "__main__":
    clf, m = train()
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(clf, MODEL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(m, indent=2))
    print({k: round(v, 3) for k, v in m.items() if isinstance(v, float)})
    print("train/test rows:", m["n_train"], m["n_test"])
