from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
def root():
    return {"status": "DMRC backend alive 🚆"}


# ----------------- Station corresponding Line -----------------

YELLOW_LINE_STATIONS = {
    "samaypur badli","rohini sector 18","haiderpur badli mor","jahangirpuri",
    "adarsh nagar","azadpur","model town","gtb nagar","vishwa vidyalaya",
    "vidhan sabha","civil lines","kashmere gate","chandni chowk","chawri bazar",
    "new delhi","rajiv chowk","patel chowk","central secretariat",
    "udyog bhawan","lok kalyan marg","jor bagh","ina","aiims","green park",
    "hauz khas","malviya nagar","saket","qutab minar","chhatarpur",
    "sultanpur","ghitorni","arjan garh","guru dronacharya","sikandarpur",
    "mg road","iffco chowk","millenium city centre"
}

BLUE_LINE_STATIONS = {
    "dwarka sector 21","dwarka sector 8","dwarka sector 9","dwarka sector 10",
    "dwarka sector 11","dwarka sector 12","dwarka sector 13","dwarka sector 14",
    "dwarka","dwarka mor","nawada","uttam nagar west","uttam nagar east",
    "janakpuri west","janakpuri east","tilak nagar","subhash nagar",
    "tagore garden","rajouri garden","ramesh nagar","moti nagar","kirti nagar",
    "shadipur","patel nagar","rajendra place","karol bagh","jhandewalan",
    "ramakrishna ashram marg","rajiv chowk","barakhamba road","mandi house",
    "supreme court","indraprastha","yamuna bank","akshardham",
    "mayur vihar phase 1","mayur vihar extension","new ashok nagar",
    "noida sector 15","noida sector 16","noida sector 18","botanical garden",
    "golf course","noida city centre","noida sector 34","noida sector 52",
    "noida sector 61","noida sector 59","noida sector 62",
    "noida electronic city","laxmi nagar","nirman vihar","preet vihar",
    "karkarduma","anand vihar","kaushambi","vaishali"
}
SUPPORTED_LINES = {"blue", "yellow"}

# ----------------- Line resolution logic -----------------

def resolve_line(station: str, line: str | None):
    s = station.lower().strip()

    in_yellow = s in YELLOW_LINE_STATIONS
    in_blue = s in BLUE_LINE_STATIONS

    if not in_yellow and not in_blue:
        return None, "UNKNOWN_STATION"

    # Interchange station
    if in_yellow and in_blue:
        if line is None:
            return None, "INTERCHANGE_REQUIRES_LINE"

        chosen_line = line.lower()

        if chosen_line not in SUPPORTED_LINES:
            return None, "LINE_NOT_SUPPORTED"

        return chosen_line, "OK"

    # Single-line station
    if in_yellow:
        return "yellow", "OK"
    if in_blue:
        return "blue", "OK"



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


# ---------------- Interchange bias ----------------

INTERCHANGE_BIAS = {
    "rajiv chowk": 0.25,
    "kashmere gate": 0.22,
    "central secretariat": 0.18,
    "hauz khas": 0.20,
    "mandi house": 0.15,
    "kirti nagar": 0.12,
    "yamuna bank": 0.10
}


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
    distance_from_end = min(coach_index - 1, 8 - coach_index)
    max_distance = 4
    pos_score = 1 - (distance_from_end / max_distance)
    crowd_score = 1 - relative_crowd
    return round(max(0, min(0.6 * pos_score + 0.4 * crowd_score, 1)), 2)


# ---------------- Main endpoint ----------------

@app.get("/predict_crowd")
def predict_crowd(
    station: str,
    hour: int,
    line: str | None = None,
    direction: str = "up",
    gender: str = "prefer_not_to_say",
    needs_accessibility: bool = False
):
    resolved_line, status = resolve_line(station, line)

    if status == "UNKNOWN_STATION":
        return {"error": "UNKNOWN_STATION"}

    if status == "INTERCHANGE_REQUIRES_LINE":
        return {
            "error": "INTERCHANGE_REQUIRES_LINE",
            "available_lines": ["blue", "yellow"]
        }

    raw = []

    # Line bias
    if resolved_line == "blue":
        line_bias = 0.2
    elif resolved_line == "yellow":
        line_bias = 0.15
    else:
        line_bias = 0.1

    # Station bias
    station_bias = INTERCHANGE_BIAS.get(station.lower(), 0.0)

    center = 4.5

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

        raw.append({"coach": coach_id, "index": i, "raw": raw_value})

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
        "line": resolved_line,
        "direction": direction,
        "hour": hour,
        "time_band": get_time_band(hour),
        "gender": gender,
        "needs_accessibility": needs_accessibility,
        "coaches": coaches
    }
