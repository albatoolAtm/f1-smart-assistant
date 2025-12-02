# app/get_real_telemetry.py

from typing import List, Dict, Any
from pathlib import Path

import fastf1


def load_real_telemetry(
    year: int = 2023,
    gp: str = "Bahrain",
    session_type: str = "R",  # "R" = Race
    driver: str = "HAM",
    lap_number: int = 10,
) -> List[Dict[str, Any]]:
    """
    Load real F1 telemetry using FastF1 and return it as
    a list of dicts (sequence of telemetry points).
    """

    # Enable cache in ./cache
    cache_dir = Path("./cache")
    cache_dir.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))

    # Load session (e.g. Bahrain 2023 Race)
    session = fastf1.get_session(year, gp, session_type)
    session.load()

    # Pick laps for the given driver (HAM, VER, etc.)
    laps = session.laps.pick_driver(driver)

    # Select requested lap
    lap = laps.loc[laps["LapNumber"] == lap_number]
    if lap.empty:
        raise ValueError(f"No lap {lap_number} found for driver {driver}")

    telemetry = lap.get_telemetry()  # pandas DataFrame

    # Track temperature (if available)
    track_temp = 40.0
    try:
        weather = session.weather_data
        if "TrackTemp" in weather:
            track_temp = float(weather["TrackTemp"].mean())
    except Exception:
        pass

    sequence: List[Dict[str, Any]] = []

    for _, row in telemetry.iterrows():
        point: Dict[str, Any] = {
            "speed": float(row.get("Speed", 0.0)),
            "throttle": float(row.get("Throttle", 0.0)),
            "brake": float(row.get("Brake", 0.0)),
            "gear": float(row.get("nGear", 0.0)),
            "steering": float(row.get("Steer", 0.0)),
            # Tyre temp is not always available → default
            "tyre_temp": float(row.get("TyreTemp", 90.0)),
            "rpm": float(row.get("RPM", 11000.0)),
            "lat_g": float(row.get("Lat", 0.0)),
            "long_g": float(row.get("Long", 0.0)),
            "track_temp": track_temp,
        }
        sequence.append(point)

    return sequence
