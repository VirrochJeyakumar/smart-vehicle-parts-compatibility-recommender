# Aim of this section is 7) Confidence Scorer

# All candidates are not all same level of confidence due to range intersection,
# how similar spacing/hyphenation in make/model, year type (4 digit more confident)
# and how many models were found in dataset

# Start at 1.0 confidence score, and negate based on penalties

# E.g. ["kawasaki", "zx6r", "07-12"]  has make = "kawasaki", 
# models = ["zx-6r"] and year_ranges = [(2007, 2012)], which gives
# output candidates = 
# [{"make": "kawasaki", 
#   "model": "zx-6r",
#   "year_start": 2007,
#   "year_end: 2012"}]
# (can have multiple tuple candidates in list for each model and year range)

def rounding(x: float) -> float:
    if x < 0.0:
        return 0.0 
    elif x > 1.0:
        return 1.0 
    else:
        return x
    
def score_tuple(text: str, candidate: Dict, original_year_start: int, original_year_end: int, year_source: str, num_models_detected: int) -> float:
    score = 1.0

    model = candidate["model"]
    # if spacing/hypening not same as in dataset
    if model not in text:
        score -= 0.10

    # type of year
    if year_source == "yy_range":
        score -= 0.05
    elif year_source == "singles":
        score -= 0.10
    
    # range intersection
    range_shift = abs(candidate["year_start"] - original_year_start) + abs(candidate["year_end"] - original_year_end)
    score -= min(0.25, 0.05 * range_shift)

    # multiple models in dataset
    if num_models_detected > 1:
        score -= 0.05 * (num_models_detected - 1)

    return rounding(score)


