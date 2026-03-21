# Aim of this section is 3) Model Detection

# Take the list ["kawasaki", "zx6r", "07-12"] and search for models for the
# identified make

# The main issue is on eBay, some sellers may be inconsistent with how they
# type the model

# For example, CarQuery has model as "zx-6r", but the seller may have it as
# "zx6r" (same model, just no space/hyphen)

# To fix this, must generate list of patterns that may match each model, e.g.
# for "zx-6r", the pattern could be "zx[- ]?6r". This pattern permits:
# "zx6r", "zx-6r" and "zx 6r"

# Then search list of tokens for each model of the idenitifed make to
# identify the model (if a model has multiple model compatability, a list
# is returned)

# E.g. for ["kawasaki", "zx6r", "07-12"], "zx-6r" is returned (as in CarQuery dataset)

import re
from typing import List, Dict, Tuple, Set, Optional

def detect_models(text: str, make: str, models_by_make: Dict[str, Set[str]]) -> List[str]:
    if not make:
        return []
    
    # 1) possible models are all models for the identified make
    possible_models = models_by_make.get(make, set())
    found = []

    # 2) for each model, check for space/hyphen variants in tokens list
    for model in possible_models:
        # put escape sign before every special character
        patt = re.escape(model.lower())

        # using regular expressions to allow hyphen or space to be space or hyphen or nothing
        patt = patt.replace(r"\-", r"[- ]?")
        patt = patt.replace(r"\ ", r"[- ]?")

        # add word boundaries to prevent matching in longer words
        pattern = r"\b" + patt + r"\b"

        if re.search(pattern, text):
            found.append(model)
    
    return found