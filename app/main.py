from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
def root():
    return {"status": "DMRC backend alive 🚆"}


# ---------------- Time logic ----------------

def get_time_band(hour: int):
    if 8 <= hour <= 10:
        return "HIGH"
    elif 17 <= hour <= 20:
        return "VERY_HIGH"
    elif 11 <= hour <= 16:
        return "MEDIUM"
    else:
        return "LOW"


def time_factor(hour: int):
    if 8 <= hour <= 10:
        return 0.9
    elif 17 <= hour <= 20:
        return 1.0
    elif 11 <= hour <= 16:
        return 0.6
    else:
        return 0.4


# ---------------- Direction bias ----------------

def direction_bias(hour: int, direction: str):
    direction = direction.lower()
    if 8 <= hour <= 10 and direction == "up":
        return 0.12
    elif 17 <= hour <= 20 and direction == "down":
        return 0.12
    else:
        return 0.0


# ---------------- Policy metadata ----------------

WOMEN_RESERVED_COACH = "C1"


def is_coach_allowed(coach: str, gender: str):
    gender = gender.lower()
    if coach == WOMEN_RESERVED_COACH:
        return gender == "woman"
    return True


# ---------------- Accessibility score ----------------

def accessibility_score(coach_index: int, relative_crowd: float):
    """
    Returns value between 0 and 1
    Higher = better accessibility
    """
    # distance from nearest end
    distance_from_end = min(coach_index - 1, 8 - coach_index)
    max_distance = 4  # middle worst

    pos_score = 1 - (distance_from_end / max_distance)
    crowd_score = 1 - relative_crowd

    score = 0.6 * pos_score + 0.4 * crowd_score
    return round(max(0, min(score, 1)), 2)


# ---------------- Main endpoint ----------------

@app.get("/predict_crowd")
def predict_crowd(
    station: str,
    hour: int,
    line: str,
    direction: str,
    gender: str,                  # man | woman | other | prefer_not_to_say
    needs_accessibility: bool
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

    center = 4.5

    # ---------- Raw crowd computation ----------
    for i in range(1, 9):
        coach_id = f"C{i}"
        distance = abs(i - center)
        coach_bias = (4 - distance) * 0.08
        noise = random.uniform(-0.03, 0.03)

        raw_value = (
            time_factor(hour)
            + direction_bias(hour, direction)
            + line_bias
            + station_bias
            + coach_bias
            + noise
        )

        raw.append({
            "coach": coach_id,
            "index": i,
            "raw": raw_value
        })

    # ---------- Relative normalization ----------
    values = [c["raw"] for c in raw]
    mn, mx = min(values), max(values)

    BASELINE = 0.35
    RANGE = 0.55

    coaches = []
    for c in raw:
        norm = (c["raw"] - mn) / (mx - mn + 1e-6)
        crowd = round(min(BASELINE + norm * RANGE, 0.95), 2)

        allowed = is_coach_allowed(c["coach"], gender)

        acc_score = (
            accessibility_score(c["index"], crowd)
            if needs_accessibility and allowed
            else None
        )

        coaches.append({
            "coach": c["coach"],
            "relative_crowd": crowd,
            "allowed_for_user": allowed,
            "women_reserved": c["coach"] == WOMEN_RESERVED_COACH,
            "accessibility_score": acc_score
        })

    return {
        "station": station,
        "line": line,
        "direction": direction,
        "hour": hour,
        "time_band": get_time_band(hour),
        "gender": gender,
        "needs_accessibility": needs_accessibility,
        "coaches": coaches
    }
