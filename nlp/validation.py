# Aim of this section is 6) Validation Against CarQuery Dataset

# Take the raw candidates of the form
# [{"make": "kawasaki", 
#   "model": "zx-6r",
#   "year_start": 2007,
#   "year_end: 2012"}]
# and check they are valid within the CarQuery dataset

# First need to check that both make and model are valid

# Then need to check if year range is valid of that make/model
# If not valid, check for any years that match and change the range
# to fit the range based on intersection of the given range and CarQuery
# dataset range

# This engineering trade-off keeps the graph correct, and still keep listings
# that are mostly correct

# E.g. ["kawasaki", "zx6r", "05-15"]  has make = "kawasaki", 
# models = ["zx-6r"] and year_ranges = [(2005, 2015)], which gives
# output candidates = 
# [{"make": "kawasaki", 
#   "model": "zx-6r",
#   "year_start": 2005,
#   "year_end: 2015"}]
# after checking CarQuery, only years 2007-2012 is valid for that make/model
# so change candidate to overlapping years:
# [{"make": "kawasaki", 
#   "model": "zx-6r",
#   "year_start": 2007,
#   "year_end: 2012"}]
# (does not extend years, i.e. if CarQuery has larger range, it is restricted to candidate range only)

from typing import List, Dict, Tuple, Set, Optional

def validation(candidates: List[Dict], year_range_by_model: Dict[Tuple[str, str], Tuple[int, int]]) -> List[Dict]:
    validated = []

    for c in candidates:
        make = c["make"]
        model = c["model"]
        key = (make, model)

        # 1) first check the make/model exists in CarQuery, else reject
        if key not in year_range_by_model:
            continue

        prod_start, prod_end = year_range_by_model[key]

        # 2) take intersection of years that match with CarQuery and given candidate
        # so that it is not wasted, nor very incorrect

        start = max(c["year_start"], prod_start)
        end = min(c["year_end"], prod_end)

        # 3) if no intersection, incorrect candidate so reject 
        if start > end: 
            continue

        # 4) keep the intersection modififed candidate tuple
        validated.append({
            "make": make,
            "model": model,
            "year_start": start,
            "year_end": end
        })

    return validated