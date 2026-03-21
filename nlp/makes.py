# Aim of this section is 2) Tokenisation and Make Detection

# Take the string and first split into tokens i.e. make, model & year
# like "kawasaki zx6r 07-12" to ["kawasaki", "zx6r", "07-12"]

# Then, identify the vehicle manufacturer (e.g. Kawasaki, Honda, Yamaha, BMW)
# from a valid set of makes from CarQuery

# The tokens are scanned, and first one that appears in the set of valid
# makes becomes the detected make

# so "kawasaki zx6r 07-12" goes to ["kawasaki", "zx6r", "07-12"]
# which then detects make as "kawasaki"

import re
from typing import List, Dict, Tuple, Set, Optional

def tokenise(text: str) -> List[str]:
    # 1) split string into tokens, where one is the make
    return text.split()

def detect_make(tokens: List[str], valid_makes: Set[str]) -> Optional[str]:
    # 2) scan valid makes for make, and if found return that
    for t in tokens:
        if t in valid_makes:
            return t
    return None