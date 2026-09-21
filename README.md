# smart-vehicle-parts-compatiblity-recommender

SMART VEHICLE PARTS COMPATIBILITY RECOMMENDER

Aftermarket vehicle parts marketplaces host millions of listings, yet locating parts that are genuinely compatible with a specific vehicle remains difficult. Compatibility information is typically embedded within informal, inconsistent free-text titles, placing a significant burdern on users who must manually interpret seller conventions and cross-reference multiple listings. This project presents a smart vehicle parts compatibility recommender that automatically extracts structured compatibility relationships from unstructured eBay Motors listings and uses the resulting data to generate cost-effective, compatibility-verified bundles of parts for a given vehicle.

The system is implemented as a staged pipeline comprising five components: data acquisition from the eBay Browse API, rule-based compatibility extraction and normalisation, graph construction in Neo4j, a recommendation engine with heuristic scoring, and bundle optimisation subject to user-specified constraints. Extracted compatibility tuples are validated against the NHTSA Vehicle Product Information Catalog to ensure correctness before entering the graph.

Results

Evaluation on a labelled dataset of 300 listing titles demonstrates 90.9% extraction precision and 84.9% coverage. A comparative analysis against a GPT-4o-mini baseline quantifies the trade-offs between precision, coverage, latency and cost, with the rule-based pipeline achieving higher precision and three-orders-of-magnitude lower latency. Graph query performance supports end-to-end recommendation in under 100 milliseconds. The system enforces hard compatibility constraints throughout, ensuring that every recommended part has a verified fitment relationship with the user's vehicle

&\*\*\*(&)

Architecture

The system is organised as a staged pipeline comprising five components: data acquisition, compatibility extraction and normalisation, graph construction, recommendation and bundle optimisation, supported by a web-based user interface. Each component consumes the output of its predecessor through a well-defined interface and can be developed, tested and refined independently.

A critical architecural distinction is the separation between offline and real-time processing. Data acquisition, extraction, normalisation, validation and graph population are performed as batch processes, while recommendation and bundle generation operate in real time against the prebuilt graph. This separation ensures that user-facing latency is determined solely by graph query performance rather than upstream processing costs, and allows the offline pipeline to be re-executed against cached data without consuming additional API quota.

Graph Schema

The graph schema comprises three node types and two relationship types. Vehicle nodes represent individual vehicle-year combinations, keyed by a composite string of the form make-model-year (for example, "kawasaki-zx6r-2010"). Each Vehicle node stores the make, model and year as separate properties for query convenience. Part nodes represent individual marketplace lisitngs, keyed by the eBay listing identifier and carrying properties including title, price, currency, condition, brand, category, URL and seller rating. Seller nodes represent vendor accounts, keyed by username and carrying the feedback percentage.

Two relationship types connect these nodes. A FITS edge connects a Part node to every Vehicle node with which part is compatibile, as determined by the extraction and validation pipeline. A SOLD_BY edge connects a Part node to the Seller node representing the vendor who listed it. This schema captures the three-way association between parts, vehicles and sellers that the recommendation engine requires - given a vehicle, the system can traverse FITS edges to find compatibile parts, then follow SOLD_BY edges to identify their vendors and associated ratings.

Recommendation Engine

The engine is implemented as a six-step pipeline: compatibility filtering, popularity scoring, category affinity analysis, individual part scoring, bundle construction and bundle optimisation. Each step is a separate function, maintaining the modularity principle and enabling independent testing and refinement.

Setup Guide

Requirements: Python 3.10+, Docker.

1. Install packages
   pip install neo4j flask requests

2. Remove Neo4j in case already started
   docker rm -f neo4j

3. Start Neo4j in Docker
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/cs310password neo4j:5

4. (OPTIONAL - TAKES TIME, DATA EXISTS ALREADY) Run crawler to get NEW listings - if viewing web app, skip this step
   python crawler/fetch_listings.py

5. Load data into Neo4j
   python graph/load_neo4j.py --uri bolt://localhost:7687 --user neo4j --password cs310password --input data

6. Start the web app
   python web/app.py --uri bolt://localhost:7687 --user neo4j --password cs310password --port 5000

7. Access the web app
   http://localhost:5000

Data

Scraped listing data is not included in this repository. Run the crawler with your own eBay keyset to regenerate it.
