"""
This is code to infer the category from the title text, added LATER because eBay does not always return a category.

This is used to support bundle construction.
"""

import re
from typing import Optional

# each category has a list of keyword patterns

CATEGORY_RULES = [
    # braking
    ("brake pads",       [r"\bbrake\s*pad", r"\bdisc\s*pad", r"\bsintered\s*pad"]),
    ("brake discs",      [r"\bbrake\s*disc", r"\bbrake\s*rotor", r"\brotor\b"]),
    ("brake lines",      [r"\bbrake\s*line", r"\bbrake\s*hose", r"\bbraided\s*line"]),
    ("brake fluid",      [r"\bbrake\s*fluid", r"\bdot[- ]?[345]"]),
    ("brake calipers",   [r"\bcaliper", r"\bbrake\s*caliper"]),
    ("brake levers",     [r"\bbrake\s*lever", r"\bclutch\s*lever", r"\blever\s*set"]),

    # drivetrain
    ("chain kit",        [r"\bchain\s*(and|&)?\s*sprocket", r"\bchain\s*kit", r"\bsprocket\s*kit", r"\bdid\s*chain", r"\bchain\s*set"]),
    ("chains",           [r"\bchain\b(?!.*sprocket)", r"\bdrive\s*chain"]),
    ("sprockets",        [r"\bsprocket", r"\bfront\s*sprocket", r"\brear\s*sprocket"]),
    ("clutch",           [r"\bclutch\s*plate", r"\bclutch\s*kit", r"\bclutch\s*disc", r"\bclutch\s*cable", r"\bclutch\s*spring"]),

    # engine/fluids
    ("oil filters",      [r"\boil\s*filter"]),
    ("air filters",      [r"\bair\s*filter", r"\bair\s*cleaner"]),
    ("spark plugs",      [r"\bspark\s*plug", r"\biridium\s*plug", r"\bngk\b.*plug"]),
    ("engine oil",       [r"\bengine\s*oil", r"\bmotor\s*oil", r"\b10w[- ]?40", r"\b5w[- ]?30"]),
    ("coolant",          [r"\bcoolant", r"\bantifreeze"]),

    # body/appearance
    ("fairings",         [r"\bfairing", r"\bbodywork", r"\bcowl", r"\bbody\s*kit"]),
    ("windshields",      [r"\bwindshield", r"\bwindscreen", r"\bwind\s*screen"]),
    ("mirrors",          [r"\bmirror"]),
    ("handlebars",       [r"\bhandlebar", r"\bclip[- ]?on", r"\bbar\s*end"]),
    ("grips",            [r"\bgrip\b", r"\bhand\s*grip", r"\bthrottle\s*grip"]),
    ("pegs",             [r"\bfoot\s*peg", r"\brearset", r"\brear\s*set"]),
    ("seats",            [r"\bseat\b(?!.*post)", r"\bseat\s*cowl", r"\bpillion"]),
    ("tank pads",        [r"\btank\s*pad", r"\btank\s*grip", r"\btank\s*protector"]),

    # lighting
    ("headlights",       [r"\bheadlight", r"\bhead\s*lamp"]),
    ("tail lights",      [r"\btail\s*light", r"\brear\s*light", r"\bled\s*tail"]),
    ("indicators",       [r"\bindicator", r"\bturn\s*signal", r"\bsignal\s*light"]),

    # suspension/wheels
    ("tyres",            [r"\btyre", r"\btire", r"\bradial"]),
    ("suspension",       [r"\bsuspension", r"\bfork\s*seal", r"\bshock\b", r"\bfork\s*oil", r"\blowering\s*kit"]),
    ("bearings",         [r"\bbearing", r"\bwheel\s*bearing", r"\bsteering\s*bearing"]),

    # exhaust
    ("exhausts",         [r"\bexhaust", r"\bsilencer", r"\bmuffler", r"\bslip[- ]?on", r"\bakrapovic", r"\byoshimura", r"\bleo\s*vince"]),

    # electrical
    ("batteries",        [r"\bbatter(?:y|ies)", r"\byuasa", r"\blithium\s*batter"]),
    ("stators",          [r"\bstator", r"\brectifier", r"\bregulator"]),
]

# CHECK ITEMS ABOVE BRANDS ETC


# classify a listing title into a part category
# return the category name or None if no match
def classify_category(title: str) -> Optional[str]:
    if not title:
        return None
    
    text = title.lower()

    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, text):
                return category
    
    return None