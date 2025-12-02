# app/sarah_model.py

from typing import List, Dict, Any

import numpy as np
import torch
import torch.nn as nn


class SimpleTelemetryModel(nn.Module):
    """
    Very simple LSTM-based model over telemetry sequence.
    Input:  (batch, seq_len, input_dim)
    Output: probability of pace drop in the next lap (0..1)
    """

    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_dim)
        _, (h_n, _) = self.lstm(x)   # h_n: (num_layers, batch, hidden_dim)
        h_last = h_n[-1]             # (batch, hidden_dim)
        logits = self.fc(h_last)     # (batch, 1)
        prob = self.sigmoid(logits)  # (batch, 1)
        return prob


DEFAULT_INPUT_DIM = 10  # must match features we build in preprocess_telemetry_sequence


def load_telemetry_model() -> SimpleTelemetryModel:
    """
    Create the telemetry model.
    (Later you can load trained weights here if you have them.)
    """
    model = SimpleTelemetryModel(input_dim=DEFAULT_INPUT_DIM)
    model.eval()
    return model


def preprocess_telemetry_sequence(raw_sequence: List[Dict[str, Any]]) -> np.ndarray:
    """
    Convert a list of telemetry dicts into a feature matrix (seq_len, input_dim).
    """
    features = []
    for point in raw_sequence:
        speed = float(point.get("speed", 0.0))
        throttle = float(point.get("throttle", 0.0))
        brake = float(point.get("brake", 0.0))
        gear = float(point.get("gear", 0.0))
        steering = float(point.get("steering", 0.0))
        tyre_temp = float(point.get("tyre_temp", 0.0))
        rpm = float(point.get("rpm", 0.0))
        lat_g = float(point.get("lat_g", 0.0))
        long_g = float(point.get("long_g", 0.0))
        track_temp = float(point.get("track_temp", 0.0))

        feature_vec = [
            speed,
            throttle,
            brake,
            gear,
            steering,
            tyre_temp,
            rpm,
            lat_g,
            long_g,
            track_temp,
        ]
        features.append(feature_vec)

    return np.array(features, dtype=np.float32)


def predict_pace_drop(
    model: SimpleTelemetryModel,
    telemetry_sequence: List[Dict[str, Any]],
) -> float:
    """
    High-level helper:
    - preprocess telemetry
    - run the model
    - return probability (0..1)
    """
    features = preprocess_telemetry_sequence(telemetry_sequence)  # (seq_len, input_dim)

    # add batch dimension
    x = torch.from_numpy(features).unsqueeze(0)  # (1, seq_len, input_dim)

    with torch.no_grad():
        prob = model(x)  # (1, 1)

    return float(prob.item())
