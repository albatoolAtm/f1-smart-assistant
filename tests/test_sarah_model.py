# tests/test_sarah_model.py

import sys
import os

# إضافة جذر المشروع لمسار الاستيراد
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(PROJECT_ROOT)

from app.get_real_telemetry import load_real_telemetry
from app.sarah_model import load_telemetry_model, predict_pace_drop


def main():
    print("Loading real telemetry (FastF1)...")
    telemetry_seq = load_real_telemetry(
        year=2023,
        gp="Bahrain",
        session_type="R",
        driver="HAM",
        lap_number=10,
    )

    print(f"Telemetry sequence length: {len(telemetry_seq)}")

    print("Initializing telemetry model...")
    model = load_telemetry_model()

    print("Running prediction...")
    prob = predict_pace_drop(model, telemetry_seq)

    print("\n=== Sarah Telemetry Model Test ===")
    print(f"Pace drop probability: {prob:.4f}")


if __name__ == "__main__":
    main()
