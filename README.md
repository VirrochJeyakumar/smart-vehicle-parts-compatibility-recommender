# smart-vehicle-parts-compatiblity-recommender

Setup Guide

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
