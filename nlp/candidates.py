# Aim of this section is 5) Make Candidate Compatibility Tuples

# Take the three identified parts (make, model and year range) and make
# a compatability tuple for each year range for each model (Cartesian product)

# Can filter out inconsistent year range to model with CarQuery database validation

# E.g. ["kawasaki", "zx6r", "07-12"]  has make = "kawasaki", 
# models = ["zx-6r"] and year_ranges = [(2007, 2012)], which gives
# output candidates = 
# [{"make": "kawasaki", 
#   "model": "zx-6r",
#   "year_start": 2007,
#   "year_end: 2012"}]
# (can have multiple tuple candidates in list for each model and year range)

from typing import List, Dict, Tuple, Set, Optional

def build_candidates(make: str, models: List[str], year_ranges: List[Tuple[int, int]]) -> List[Dict]:
    candidates = []
    if not make or not models or not year_ranges:
        return candidates
    
    # do Cartesian product to filter later

    # for each model, do each year range possibility and then filter using
    # CarQuery for validation
    for model in models:
        for start, end in year_ranges:
            candidates.append({
                "make": make,
                "model": model,
                "year_start": start,
                "year_end": end,
            })

    return candidates