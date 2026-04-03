"""
Recommendation engine code, which works in 6 steps:

1) Compatibility filtering - find all parts that fit a vehicle
2) Popularity scoring - count how many vehicles each part fits
3) Co-occurrence analysis - find parts that commonly appear together
4) Individual part scoring - score each part (price, seller, popularity)
5) Bundle construction - group by category & build candidate bundles
6) Bundle optimisation - apply user constraints & rank final bundles
"""

from typing import List, Dict, Optional, Tuple
from itertools import product as cartesian_product
from itertools import combinations


# 1) Compatibility Filtering

# user picks a vehicle (make, model, year)
# graph is traversed to find every Part node connected via a FITS edge to that Vehicle node


# query Neo4j for all parts compatible with given vehicle
# returns list of dicts with part info & seller
def get_compatible_parts(driver, make: str, model: str, year: int) -> List[Dict]:
    query = """
    MATCH (p:Part)-[:FITS]->(v:Vehicle {make: $make, model: $model, year: $year})
    OPTIONAL MATCH (p)-[:SOLD_BY]->(s:Seller)
    RETURN  p.listing_id    AS listing_id,
            p.title         AS title,
            p.price         AS price,
            p.currency      AS currency,
            p.category      AS category,
            p.condition     AS condition,
            p.brand         AS brand,
            p.url           AS url,
            p.seller_rating AS seller_rating,
            s.username      AS seller
    """

    records, _, _ = driver.execute_query(
        query,
        make=make, model=model, year=year,
        database_="neo4j",
    )
    return [dict(r) for r in records]


# 2) Popularity Scoring

# popularity = how many distinct vehicles does this part fit?
# a part that fits 20 different vehicles is probably more a common/trusted part
# than one that only fits 1 (useful signal for ranking)


# for each part, count how many vehicles it fits
# returns {listing_id: vehicle_count}
def get_popularity(driver, listing_ids: List[str]) -> Dict[str, int]:
    if not listing_ids:
        return {}
    
    query = """
    MATCH (p:Part)-[:FITS]->(v:Vehicle)
    WHERE p.listing_id IN $ids
    RETURN p.listing_id AS listing_id, count(DISTINCT v) as vehicle_count
    """

    records, _, _ = driver.execute_query(
        query,
        ids=listing_ids,
        database_="neo4j",
    )
    return {r["listing_id"]: r["vehicle_count"] for r in records}


# CHECK REPORT FOR CHANGE
# 3) Category Affinity Analysis

# instead of counting shared vehicles (popularity), domain knowledge is used
# about which part categories naturally go together


# category affinity map
# defines how well categories pair together in a bundle
# 0-1 scale, where higher = more natural pairing
# e.g. brake discs + brake pads = 0.9
# pairs not listed default to 0.1
# same category pairs are 0.0

CATEGORY_AFFINITY = {
    # braking
    ("brake pads", "brake discs"):     0.9,
    ("brake pads", "brake lines"):     0.8,
    ("brake pads", "brake fluid"):     0.7,
    ("brake discs", "brake lines"):    0.7,
    ("brake discs", "brake fluid"):    0.6,
    ("brake pads", "brake levers"):    0.5,

    # drivetrain
    ("chain kit", "engine oil"):       0.7,
    ("chain kit", "sprockets"):        0.8,
    ("chains", "sprockets"):           0.9,

    # engine maintenance
    ("oil filters", "engine oil"):     0.9,
    ("oil filters", "spark plugs"):    0.7,
    ("air filters", "spark plugs"):    0.7,
    ("air filters", "oil filters"):    0.6,
    ("engine oil", "spark plugs"):     0.6,

    # service kit combos
    ("brake pads", "oil filters"):     0.5,
    ("brake pads", "chain kit"):       0.5,
    ("brake pads", "spark plugs"):     0.4,
    ("oil filters", "chain kit"):      0.5,
    ("air filters", "chain kit"):      0.4,
    ("air filters", "engine oil"):     0.5,

    # body
    ("fairings", "windshields"):       0.6,
    ("fairings", "mirrors"):           0.5,
}

DEFAULT_AFFINITY = 0.1

# get affinity value between two categories
def get_affinity(cat1: str, cat2: str) -> float:
    if cat1 == cat2:
        return 0.0
    key = tuple(sorted([cat1, cat2]))
    return CATEGORY_AFFINITY.get(key, DEFAULT_AFFINITY)


# for each pair of parts, look up category affinity
# returns nested dict: {id1: {id2: affinity_score}}
def get_category_affinities(parts: List[Dict]) -> Dict[str, Dict[str, float]]:
    affinities = {}
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            cat1 = parts[i].get("category") or "uncategorised"
            cat2 = parts[j].get("category") or "uncategorised"
            score = get_affinity(cat1, cat2)
            if score > 0:
                id1 = parts[i]["listing_id"]
                id2 = parts[j]["listing_id"]
                affinities.setdefault(id1, {})[id2] = score
                affinities.setdefault(id2, {})[id1] = score
    return affinities



# 4) Individual Part Scoring

# each part gets a score from 0 to 1 based on 3 features:
# - price (cheaper is better)
# - seller (higher seller rating is better)
# - popularity (more vehicle fits = more popular)
# these are combined with configurable weights

DEFAULT_WEIGHTS = {
    "price": 0.4,
    "seller": 0.3,
    "popularity": 0.3,
}

# adds overall score and individual sub-scores to each part dict
# returns parts sorted by score descending
def score_parts(parts: List[Dict], popularity: Dict[str, int], weights: Dict[str, float] = None,) -> List[Dict]:
    if not parts:
        return []
    
    w = weights or DEFAULT_WEIGHTS

    prices = []
    ratings = []
    pops = []

    for p in parts:
        price = _to_float(p.get("price"))
        rating = _to_float(p.get("seller_rating"))
        pop = popularity.get(p["listing_id"], 1)
        prices.append(price)
        ratings.append(rating)
        pops.append(pop)
    
    # LOOK AT THIS
    max_price = max((x for x in prices if x is not None), default=1)
    min_price = min((x for x in prices if x is not None), default=0)
    max_pop = max(pops) if pops else 1

    scored = []
    for i, p in enumerate(parts):
        price = prices[i]
        if price is not None and max_price > min_price:
            price_score = 1.0 - (price - min_price) / (max_price - min_price)
        else:
            # default price score of neutral 0.5 if price missing
            price_score = 0.5
    
        rating = ratings[i]
        if rating is not None:
            seller_score = min(rating / 100.0, 1.0)
        else:
            # default seller score of neutral 0.5 if rating missing
            price_score = 0.5
        
        pop = pops[i]
        popularity_score = pop / max_pop if max_pop > 0 else 0.0

        # weighted combination
        total = w["price"] * price_score + w["seller"] * seller_score + w["popularity"] * popularity_score

        part_with_score = dict(p)
        part_with_score["price_score"] = round(price_score, 3)
        part_with_score["seller_score"] = round(seller_score, 3)
        part_with_score["popularity_score"] = round(popularity_score, 3)
        part_with_score["score"] = round(total, 3)
        scored.append(part_with_score)
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored



# 5) Bundle Construction

# bundle = 1 part from each relevant category
# for example, if user's vehicle has compatible brake pads, brake discs and oil filters,
# a bundle might pick the best brake pad + best brake disc + best oil filter

# approach is to:
# - group scored parts by category
# - take top N parts per category
# - form bundles as the Cartesian product (1 from each category)
# - score each bundle on: total price, mean part score, vendor count


# group parts by category & take top parts from each
# then build bundles as combinations across categories
def build_bundles(scored_parts: List[Dict], co_occurrences: Dict[str, Dict[str, int]] = None, top_per_category: int = 3, max_categories: int = 3, max_bundles: int = 50,) -> List[Dict]:
    if not scored_parts:
        return []
    
    # group by category
    by_category: Dict[str, List[Dict]] = {}
    for p in scored_parts:
        cat = p.get("category") or "uncategorised"
        by_category.setdefault(cat, []).append(p)
    
    if len(by_category) < 2:
        return _single_category_ranking(scored_parts)
    
    #### CHECK NEWLY ADDED BUNDLE METHOD CHECKING AFFINITY FIRST, THEN PARTS
    # take top N from each category
    category_candidates = {}
    for cat, parts in by_category.items():
        # parts already sorted by score from Individual Part Scoring (Step 4)
        category_candidates[cat] = parts[:top_per_category]
    
    all_cats = list(category_candidates.keys())

    combo_scores = []
    # score every possible combination
    for combo in combinations(all_cats, min((max_categories), len(all_cats))):
        # average affinity between all pairs in this combo
        pair_count = 0
        total_affinity = 0.0
        for i in range(len(combo)):
            for j in range(i + 1, len(combo)):
                total_affinity += get_affinity(combo[i], combo[j])
                pair_count += 1
        avg_affinity = total_affinity / pair_count if pair_count > 0 else 0

        # average best part score across these categories
        avg_part_score = sum(category_candidates[c][0].get("score", 0) for c in combo) / len(combo)

        # combined is 60% affinity, 40% part quality
        combined = 0.6 * avg_affinity + 0.4 * avg_part_score
        combo_scores.append((combined, combo))

    combo_scores.sort(reverse=True)

    # take top 3 category combinations for variety
    top_combos = combo_scores[:3] if len(combo_scores) >= 3 else combo_scores

    all_bundles = []
    seen_bundles = set()

    for _, combo_cats in top_combos:
        cats = list(combo_cats)

        deduped_candidates = {}
        for c in cats:
            deduped_candidates[c] = deduplicate_parts(category_candidates[c])[:top_per_category]

        candidate_lists = [deduped_candidates[c] for c in cats]

        for combo in cartesian_product(*candidate_lists):
            bundle_key = tuple(sorted(p["listing_id"] for p in combo if isinstance(p, dict)))
            if bundle_key in seen_bundles:
                continue
            seen_bundles.add(bundle_key)

            bundle = _score_bundle(list(combo), co_occurrences)
            all_bundles.append(bundle)

            if len(all_bundles) >= max_bundles:
                break

        if len(all_bundles) >= max_bundles:
            break

    all_bundles.sort(key=lambda b: b["bundle_score"], reverse=True)
    return all_bundles
    ##########


# score a single bundle based on:
# - total price (sum of all part prices)
# - mean score (average of all individual part scores)
# - vendor convenience (fewer unique sellers = better)
# - co-occurrence strength (how often these parts appear together)
def _score_bundle(parts: List[Dict], co_occurrences: Dict[str, Dict[str, int]] = None,) -> Dict:
    # total price
    prices = [_to_float(p.get("price")) for p in parts]
    valid_prices = [x for x in prices if x is not None]
    total_price = sum(valid_prices) if valid_prices else 0

    # mean individual part score
    mean_score = sum(p.get("score", 0) for p in parts) / len(parts) if parts else 0

    # vendor convenience
    sellers = set(p.get("seller") for p in parts if p.get("seller"))
    num_sellers = max(len(sellers), 1)
    vendor_convenience = 1.0 / num_sellers

    # category affinity
    co_strength = 0.0
    if co_occurrences and len(parts) > 1:
        pair_count = 0
        total_affinity = 0.0
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                cat1 = parts[i].get("category") or "uncategorised"
                cat2 = parts[j].get("category") or "uncategorised"
                total_affinity += get_affinity(cat1, cat2)
                pair_count += 1
        if pair_count > 0:
            co_strength = total_affinity / pair_count

    # combine into final bundle score
    bundle_score = 0.35 * mean_score + 0.25 * vendor_convenience + 0.2 * co_strength * (1.0 / (1.0 + total_price / 100.0))

    return {
        "parts": parts,
        "categories": [p.get("category", "uncategorised") for p in parts],
        "total_price": round(total_price, 2),
        "currency": parts[0].get("currency", "GBP") if parts else "GBP",
        "mean_part_score": round(mean_score, 3),
        "num_sellers": num_sellers,
        "seller_names": sorted(sellers),
        "vendor_convenience": round(vendor_convenience, 3),
        "co_occurrence_strength": round(co_strength, 2),
        "bundle_score": round(bundle_score, 3),
    }



# when all parts same category, return each part as its own item bundle
# as there is no cross-category bundle to make
def _single_category_ranking(parts: List[Dict]) -> List[Dict]:
    bundles = []
    for p in parts:
        bundles.append({
            "parts": [p],
            "categories": [p.get("category", "uncategorised")],
            "total_price": round(_to_float(p.get("price")) or 0, 2),
            "currency": p.get("currency", "GBP"),
            "mean_part_score": p.get("score", 0),
            "num_sellers": 1,
            "seller_names": [p.get("seller")] if p.get("seller") else [],
            "vendor_convenience": 1.0,
            "co_occurrence_strength": 0,
            "bundle_score": p.get("score", 0),
        })
    return bundles



# 6) Bundle Optimisation

# apply user constraints to filter and re-rank the bundles

# constraints:
# - max budget = total bundle price must be under this
# - max vendors = bundle must not user more than N different sellers
# - required categories = user can require certain categories

# after filtering, bundles are re-sorted by score


# filter bundles by user constraints and return the final ranked list
def optimise_bundles(bundles: List[Dict], max_budget: Optional[float] = None, max_vendors: Optional[int] = None, required_categories: Optional[List[str]] = None,) -> List[Dict]:
    filtered = []
    for b in bundles:
        if max_budget is not None and b["total_price"] > max_budget:
            continue
        if max_vendors is not None and b["num_sellers"] > max_vendors:
            continue
        if required_categories:
            bundle_cats = set(b["categories"])
            if not all(rc in bundle_cats for rc in required_categories):
                continue
        filtered.append(b)

    filtered.sort(key=lambda b: b["bundle_score"], reverse=True)
    return filtered


# main running entry point using all 6 steps together into a single functional call
# user provides a vehicle and optional constraints, and gets back a list of bundles

# returns dict with vehicle info, all compatible parts and ranked bundles
def recommend(driver, make: str, model: str, year: int, max_budget: Optional[float] = None, max_vendors: Optional[int] = None, required_categories: Optional[List[str]] = None, weights: Dict[str, float] = None, top_per_category: int = 3, max_categories: int = 3, max_bundles: int = 50,) -> Dict:
    # step 1) get all compatible parts
    parts = get_compatible_parts(driver, make, model, year)
    if not parts:
        return {
            "vehicle": {"make": make, "model": model, "year": year},
            "total_compatible_parts": 0,
            "parts": [],
            "bundles": [],
            "message": "No compatible parts found for this vehicle.",
        }
    
    listing_ids = [p["listing_id"] for p in parts]

    # step 2) get popularity counts
    popularity = get_popularity(driver, listing_ids)

    # step 3) get co-occurrence data
    co_occurrences = get_category_affinities(parts)

    # step 4) score individual parts
    scored = score_parts(parts, popularity, weights)

    # step 5) build candidate bundles
    bundles = build_bundles(scored, co_occurrences, top_per_category, max_categories, max_bundles)

    # step 6) apply user constraints
    final_bundles = optimise_bundles(bundles, max_budget=max_budget, max_vendors=max_vendors, required_categories=required_categories,)

    return {
        "vehicle": {"make": make, "model": model, "year": year},
        "total_compatible_parts": len(parts),
        "categories_found": sorted(set(p.get("category") or "uncategorised" for p in parts)),
        "parts": scored,
        "bundles": final_bundles,
    }


# helper functions


# deduplication helpers to remove similar parts between different bundles being suggested
import re as _re

# reduce title to a rough product fingerprint for deduplication
def _normalise_title_for_dedup(title: str) -> str:
    t = title.lower()
    t = _re.sub(r"[£$€]\d+[\.\d]*", "", t)
    t = _re.sub(r"\b\d{4}[-/]\d{4}\b", "", t)
    t = _re.sub(r"\b\d{2}[-/]\d{2}\b", "", t)
    t = _re.sub(r"[^a-z0-9 ]", " ", t)
    t = _re.sub(r"\s+", " ", t).strip()
    return t[:40]

# keep only the best-scored part per unique product fingerprint
def deduplicate_parts(parts: List[Dict]) -> List[Dict]:
    seen = {}
    for p in parts:
        key = _normalise_title_for_dedup(p.get("title", ""))
        if key not in seen or p.get("score", 0) > seen[key].get("score", 0):
            seen[key] = p
    return list(seen.values())


# convert value to float helper
def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
