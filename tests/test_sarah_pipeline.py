# tests/test_sarah_pipeline.py

import sys
import os

# 👇 نفس الهيدر اللي في test_sarah_model.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.get_real_telemetry import load_real_telemetry
from app.sarah_model import load_telemetry_model, predict_pace_drop


def main():
    print("Loading real telemetry for pipeline test...")
    telemetry_seq = load_real_telemetry(
        year=2023,
        gp="Bahrain",
        session_type="R",
        driver="HAM",
        lap_number=12,   # نختبر لفة مختلفة عن test_sarah_model
    )

    print(f"Telemetry sequence length: {len(telemetry_seq)}")

    print("Initializing telemetry model...")
    model = load_telemetry_model()

    print("Running prediction...")
    prob = predict_pace_drop(model, telemetry_seq)

    evidence = {
        "source": "telemetry_model",
        "text": (
            f"Telemetry AI model estimates a {prob * 100:.1f}% probability of "
            f"pace drop on the lap following lap 12 for driver HAM."
        ),
        "score": prob,
        "lap": 12,
        "meta": {
            "model": "SimpleTelemetryModel",
            "year": 2023,
            "gp": "Bahrain",
            "driver_code": "HAM",
        },
    }

    print("\n=== Sarah Pipeline Test ===")
    print("Evidence object created by pipeline:")
    print(evidence)


if __name__ == "__main__":
    main()
