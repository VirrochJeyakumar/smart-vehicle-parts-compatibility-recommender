####### CAN REMOVE THIS FILE, only dataset needed

import os
import json
import time
import requests
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE_DIR, "vehicle_registry.json")

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_json(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def norm(s: str) -> str:
    return (s or "").strip().lower()

# vPIC GetModelsForMakeYear expects modelyear > 1995
START_YEAR = 1996
END_YEAR = 2024

# Keep this tight and relevant to your crawler terms (edit as you like)
MAKES_OF_INTEREST = [
    "bmw",
    "honda",
    "kawasaki",
    "yamaha",
    "suzuki",
    "ducati",
    "triumph",
    "ktm",
    "harley davidson",
    "audi",
    "mercedes-benz",
    "toyota",
    "ford",
    "volkswagen",
]

seen_years = {}  # (make, model) -> set(years)

for year in range(START_YEAR, END_YEAR + 1):
    print(f"Year {year}...")

    for make_raw in MAKES_OF_INTEREST:
        make = norm(make_raw)
        make_encoded = quote(make)

        url = (
            f"https://vpic.nhtsa.dot.gov/api/vehicles/"
            f"GetModelsForMakeYear/make/{make_encoded}/modelyear/{year}?format=json"
        )

        data = get_json(url)
        results = data.get("Results", [])

        # If make/year combo has nothing, that's fine
        for row in results:
            mk = norm(row.get("Make_Name") or row.get("MakeName") or make)
            model = norm(row.get("Model_Name") or row.get("ModelName"))
            if not mk or not model:
                continue
            seen_years.setdefault((mk, model), set()).add(year)

        time.sleep(0.1)  # be polite

# Convert sightings -> ranges
vehicles = []
for (mk, model), ys in seen_years.items():
    vehicles.append({
        "make": mk,
        "model": model,
        "year_start": min(ys),
        "year_end": max(ys),
    })

vehicles.sort(key=lambda x: (x["make"], x["model"], x["year_start"]))

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(vehicles, f, indent=2, ensure_ascii=False)

print(f"Saved {len(vehicles)} entries to {OUT_FILE}")
print("Example:", vehicles[0] if vehicles else "No data")