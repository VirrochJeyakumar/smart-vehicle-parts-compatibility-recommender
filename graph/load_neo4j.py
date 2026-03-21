"""
Build a Neo4j graph, where each node is either a vehicle tuple or a part from listing.
Each edge represents compatibility (FITS) between a vehicle and a part.

Using JSON listings.
"""

import argparse
import glob
import json
import os
from typing import Dict, Iterable, List, Optional

# method to convert value to float
def to_float(value: Optional[object]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
    
# take listings vehicle compatibility and split year ranges into each year
def expand_vehicles(compatibility: List[Dict]) -> List[Dict]:
    vehicles = []
    seen = set()

    for c in compatibility:
        make = c.get("make")
        model = c.get("model")
        year_start = c.get("year_start")
        year_end = c.get("year_end")

        if not make or not model:
            continue
        if not isinstance(year_start, int) or not isinstance(year_end, int):
            continue
        if year_start > year_end:
            continue

        for year in range(year_start, year_end + 1):
            key = f"{make}|{model}|{year}"
            if key in seen:
                continue
            seen.add(key)
            vehicles.append({
                "key": key,
                "make": make,
                "model": model,
                "year": year,
            })

    return vehicles

# stream listing dicts from one or more JSON files
def iterate_listings_from_paths(paths: Iterable[str]) -> Iterable[Dict]:
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, list):
            for row in payload:
                if isinstance(row, dict):
                    yield row

# decide which JSON files to load based on input
def resolve_input_paths(input_path: str) -> List[str]:
    if os.path.isdir(input_path):
        return sorted(glob.glob(os.path.join(input_path, "listings_*.json")))
    return [input_path]

# convert one listing into row format used in Neo4j
def build_part_row(raw: Dict) -> Optional[Dict]:
    listing_id = raw.get("listing_id")
    compatibility = raw.get("compatibility") or []
    if not listing_id or not isinstance(compatibility, list):
        return None
    
    vehicles = expand_vehicles(compatibility)
    if not vehicles:
        return None
    
    return {
        "listing_id": str(listing_id),
        "title": raw.get("title"),
        "price": to_float(raw.get("price")),
        "currency": raw.get("currency"),
        "condition": raw.get("condition"),
        "brand": raw.get("brand"),
        "category": raw.get("category"),
        "url": raw.get("url"),
        "seller": raw.get("seller"),
        "seller_rating": raw.get("seller_rating"),
        "location": raw.get("location"),
        "search_term": raw.get("search_term"),
        "vehicles": vehicles,
    }

# create Neo4j uniqueness constraints so MERGE is fast and prevent duplicates
def create_constraints(driver) -> None:
    queries = [
        "CREATE CONSTRAINT vehicle_key IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.key IS UNIQUE",
        "CREATE CONSTRAINT part_id IF NOT EXISTS FOR (p:Part) REQUIRE p.listing_id IS UNIQUE",
        "CREATE CONSTRAINT seller_name IF NOT EXISTS FOR (s:Seller) REQUIRE s.username IS UNIQUE",
    ]
    for q in queries:
        driver.execute_query(q, database_="neo4j")

# write a batch of cleaned rows into Neo4j using one query
def upsert_batch(driver, rows: List[Dict]) -> None:
    if not rows:
        return
    
    query = """
    UNWIND $rows AS row
    MERGE (p:Part {listing_id: row.listing_id})
    SET p.title = row.title,
        p.price = row.price,
        p.currency = row.currency,
        p.condition = row.condition,
        p.brand = row.brand,
        p.category = row.category,
        p.url = row.url,
        p.seller_rating = row.seller_rating,
        p.location = row.location,
        p.search_term = row.search_term
    FOREACH (_ IN CASE WHEN row.seller IS NULL THEN [] ELSE [1] END |
        MERGE (s:Seller {username: row.seller})
        SET s.feedback_percentage = row.seller_rating
        MERGE (p)-[:SOLD_BY]->(s)
    )
    WITH p, row
    UNWIND row.vehicles AS v
    MERGE (veh:Vehicle {key: v.key})
      ON CREATE SET
        veh.make = v.make,
        veh.model = v.model,
        veh.year = v.year
    MERGE (p)-[:FITS]->(veh)
    """

    driver.execute_query(query, rows=rows, database_="neo4j")

# main method of pipeline
def main() -> None:
    parser = argparse.ArgumentParser(description="Load listing compatibility JSON into Neo4j.")
    parser.add_argument("--uri", required=True, help="Neo4j URI, e.g. bolt://localhost:7687")
    parser.add_argument("--user", required=True, help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--input", default="data", help="JSON file path or directory of listings_*.json")
    parser.add_argument("--batch-size", type=int, default=200, help="Rows per write query")
    args = parser.parse_args()

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: neo4j driver. Install with 'pip install neo4j'."
        ) from exc
    
    paths = resolve_input_paths(args.input)
    if not paths:
        raise SystemExit(f"No input files found at: {args.input}")
    
    with GraphDatabase.driver(args.uri, auth=(args.user, args.password)) as driver:
        create_constraints(driver)

        batch = []
        processed = 0
        inserted = 0

        for raw in iterate_listings_from_paths(paths):
            processed += 1
            row = build_part_row(raw)
            if not row:
                continue

            batch.append(row)
            inserted += 1

            if len(batch) >= args.batch_size:
                upsert_batch(driver, batch)
                batch = []
        
        if batch:
            upsert_batch(driver, batch)

    print(f"Processed lisitngs: {processed}")
    print(f"Inserted/updated parts {inserted}")
    print(f"Input files: {len(paths)}")

if __name__ == "__main__":
    main()