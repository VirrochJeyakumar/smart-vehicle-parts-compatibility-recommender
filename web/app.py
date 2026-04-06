"""
Flask API & React frontend for the Smart Vehicle Parts Compatibility Recommender.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, send_from_directory, request, jsonify
from recommend.engine import recommend

app = Flask(__name__, static_folder="static")
driver = None


# graph database queries (from Neo4j)

def get_makes():
    records, _, _ = driver.execute_query(
        "MATCH (v:Vehicle) RETURN DISTINCT v.make AS make ORDER BY make",
        database_="neo4j"
    )
    return [r["make"] for r in records]

def get_models(make):
    records, _, _ = driver.execute_query(
        "MATCH (v:Vehicle {make: $make}) RETURN DISTINCT v.model AS model ORDER BY model",
        make=make, database_="neo4j"
    )
    return [r["model"] for r in records]

def get_years(make, model):
    records, _, _ = driver.execute_query(
        "MATCH (v:Vehicle {make: $make, model: $model}) RETURN DISTINCT v.year AS year ORDER BY year",
        make=make, model=model, database_="neo4j"
    )
    return [r["year"] for r in records]

def get_stats():
    stats = {}
    for label in ["Part", "Vehicle", "Seller"]:
        records, _, _ = driver.execute_query(f"MATCH (n:{label}) RETURN count(n) AS n", database_="neo4j")
        stats[label.lower() + "s"] = records[0]["n"] if records else 0
    records, _, _ = driver.execute_query("MATCH ()-[r:FITS]->() RETURN count(r) AS n", database_="neo4j")
    stats["fits_edges"] = records[0]["n"] if records else 0
    return stats


# API routes

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/makes")
def api_makes():
    return jsonify(get_makes())


@app.route("/api/models/<make>")
def api_models(make):
    return jsonify(get_models(make))


@app.route("/api/years/<make>/<model>")
def api_years(make, model):
    return jsonify(get_years(make, model))


@app.route("/api/recommend")
def api_recommend():
    make = request.args.get("make", "").strip()
    model = request.args.get("model", "").strip()
    year = request.args.get("year", type=int)
    max_budget = request.args.get("budget", type=float) or None
    max_vendors = request.args.get("vendors", type=int) or None
    max_categories = request.args.get("bundle_size", default=3, type=int)

    if not make or not model or not year:
        return jsonify({"error": "Missing vehicle selection"}), 400
    
    start = time.perf_counter()
    result = recommend(driver, make, model, year, max_budget=max_budget, max_vendors=max_vendors, max_categories=max_categories)
    elapsed = round((time.perf_counter() - start) * 1000, 1)
    result["elapsed_ms"] = elapsed

    return jsonify(result)


# main code starts here

def main():
    global driver

    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--port", default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    driver.verify_connectivity()
    print(f"Connected to Neo4j at {args.uri}")
    print(f"Open http://localhost:{args.port} in your browser")

    app.run(host="0.0.0.0", port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

