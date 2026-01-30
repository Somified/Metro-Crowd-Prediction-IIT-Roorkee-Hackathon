from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
def root():
    return {"status": "DMRC backend alive 🚆"}


# --- UX severity (for color palettes) ---
def get_time_band(hour: int, is_weekend: bool):
    if is_weekend:
        if 12 <= hour <= 18:
            return "MEDIUM"
        else:
            return "LOW"
    else:
        if 8 <= hour <= 10:
            return "HIGH"
        elif 17 <= hour <= 20:
            return "VERY_HIGH"
        elif 11 <= hour <= 16:
            return "MEDIUM"
        else:
            return "LOW"


# --- absolute demand by time ---
def time_factor(hour: int):
    if 8 <= hour <= 10:
        return 0.9
    elif 17 <= hour <= 20:
        return 1.0
    elif 11 <= hour <= 16:
        return 0.6
    else:
        return 0.4


# up: Dwarka ➜ Noida
# down: Noida ➜ Dwarka
def direction_bias(hour: int, direction: str):
    direction = direction.lower()
    if 8 <= hour <= 10 and direction == "up":
        return 0.12
    elif 17 <= hour <= 20 and direction == "down":
        return 0.12
    else:
        return 0.0


@app.get("/predict_crowd")
def predict_crowd(
    station: str,
    hour: int,
    line: str,
    direction: str,
    is_weekend: bool
):
    raw = []

    # Line bias
    if line.lower() == "blue":
        line_bias = 0.2
    elif line.lower() == "yellow":
        line_bias = 0.15
    else:
        line_bias = 0.1

    # Station bias
    station_bias = 0.25 if station.lower() == "rajiv chowk" else 0.0

    # Weekend multiplier (system-level)
    weekend_multiplier = 0.75 if is_weekend else 1.0

    center = 4.5  # middle of 8 coaches

    # --- raw crowd calculation ---
    for i in range(1, 9):
        distance = abs(i - center)
        coach_bias = (4 - distance) * 0.08
        noise = random.uniform(-0.03, 0.03)

        raw_value = (
            (
                time_factor(hour)
                + direction_bias(hour, direction)
                + line_bias
                + station_bias
            ) * weekend_multiplier
            + coach_bias
            + noise
        )

        raw.append({"coach": f"C{i}", "raw": raw_value})

    # --- relative normalization ---
    values = [c["raw"] for c in raw]
    mn, mx = min(values), max(values)

    BASELINE = 0.35
    RANGE = 0.55

    coaches = []
    for c in raw:
        norm = (c["raw"] - mn) / (mx - mn + 1e-6)
        crowd = BASELINE + norm * RANGE
        crowd = round(min(crowd, 0.95), 2)

        coaches.append({
            "coach": c["coach"],
            "relative_crowd": crowd
        })

    return {
        "station": station,
        "line": line,
        "direction": direction,
        "hour": hour,
        "is_weekend": is_weekend,
        "time_band": get_time_band(hour, is_weekend),
        "coaches": coaches
    }
