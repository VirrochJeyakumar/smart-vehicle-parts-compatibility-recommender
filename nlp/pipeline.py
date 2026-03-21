"""
Weeks 5-6: Complete NLP module for converting unstructured listing text.
"""

import json
from typing import List, Dict, Tuple, Set, Optional

from nlp.normalise import normalise_text
from nlp.models import detect_models
from nlp.years import extract_year_ranges
from nlp.candidates import build_candidates
from nlp.validation import validation
from nlp.makes import tokenise, detect_make

# VEHICLE_REGISTRY_FILE = "dataset/vehicle_registry.json"

# Helper builders to get list of makes, models, etc.

def load_vehicle_registry(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def build_valid_makes(registry: List[Dict]) -> Set[str]:
    return {row["make"] for row in registry if "make" in row}

def build_models_by_make(registry: List[Dict]) -> Dict[str, Set[str]]:
    out: dict[str, set[str]] = {}
    for row in registry:
        make = row.get("make")
        model = row.get("model")
        if make and model:
            out.setdefault(make, set()).add(model)
    return out

def build_year_range_by_model(registry: List[Dict]) -> Dict[Tuple[str, str], Tuple[int, int]]:
    out: Dict[Tuple[str, str], Tuple[int, int]] = {}
    for row in registry:
        make = row.get("make")
        model = row.get("model")
        ys = row.get("year_start")
        ye = row.get("year_end")
        if make and model and isinstance(ys, int) and isinstance(ye, int):
            out[(make, model)] = (ys, ye)
    return out

# Building indexes once
def build_index_from_registry(registry: List[Dict]):
    valid_makes = build_valid_makes(registry)
    models_by_make = build_models_by_make(registry)
    year_range_by_model = build_year_range_by_model(registry)
    return valid_makes, models_by_make, year_range_by_model

# Main extraction pipeline
def extract_compatibility(title: str, index) -> List[Dict]:
    # NLP end-to-end pathway:
    # normalise -> tokenise -> detect make -> detect models -> extract years
    # -> build candidates -> validate -> return final tuples
    if not title:
        return []
    
    valid_makes, models_by_make, year_range_by_model = index

    text = normalise_text(title)
    if not text:
        return []
    
    tokens = tokenise(text)

    make = detect_make(tokens, valid_makes)
    if not make:
        return []

    models = detect_models(text, make, models_by_make)
    if not models:
        return []
    
    year_ranges = extract_year_ranges(text)
    if not year_ranges:
        return []
    
    candidates = build_candidates(make, models, year_ranges)
    if not candidates:
        return []
    
    validated = validation(candidates, year_range_by_model)

    return validated
