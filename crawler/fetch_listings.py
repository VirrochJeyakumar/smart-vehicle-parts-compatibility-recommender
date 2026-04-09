"""
Weeks 3-4: Implement Crawler to fetch listings using eBay's Finder API.
"""

import os, sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from nlp.pipeline import load_vehicle_registry, build_index_from_registry, extract_compatibility
from nlp.categories import classify_category

REGISTRY_FILE = os.path.join(PROJECT_ROOT, "dataset", "vehicle_registry.json")
registry = load_vehicle_registry(REGISTRY_FILE)
index = build_index_from_registry(registry)

# 1) Configure the crawler with eBay Devloper Program details.

CLIENT_ID = "***REMOVED***"
CLIENT_SECRET = "***REMOVED***"

API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"

TOKEN_FILE = os.path.join(PROJECT_ROOT, "token.json")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_FILE = os.path.join(PROJECT_ROOT, "logs/crawler.log")

# example search terms
SEARCH_TERMS = [
    # ── Kawasaki ZX-6R ──
    "Kawasaki ZX6R brake pads",
    "Kawasaki ZX6R chain sprocket kit",
    "Kawasaki ZX6R oil filter",
    "Kawasaki ZX6R air filter",
    "Kawasaki ZX6R fairing",
    "Kawasaki ZX6R exhaust",
    "Kawasaki ZX6R clutch",
 
    # ── Kawasaki ZX-10R ──
    "Kawasaki ZX10R brake pads",
    "Kawasaki ZX10R chain sprocket kit",
    "Kawasaki ZX10R oil filter",
    "Kawasaki ZX10R fairing",
    "Kawasaki ZX10R exhaust",
 
    # ── Kawasaki Ninja 650 ──
    "Kawasaki Ninja 650 brake pads",
    "Kawasaki Ninja 650 oil filter",
    "Kawasaki Ninja 650 chain kit",
    "Kawasaki Ninja 650 exhaust",
 
    # ── Kawasaki Z900 ──
    "Kawasaki Z900 brake pads",
    "Kawasaki Z900 oil filter",
    "Kawasaki Z900 exhaust",
 
    # ── Yamaha YZF-R6 ──
    "Yamaha YZF-R6 brake pads",
    "Yamaha YZF-R6 chain sprocket kit",
    "Yamaha YZF-R6 oil filter",
    "Yamaha YZF-R6 air filter",
    "Yamaha YZF-R6 fairing",
    "Yamaha YZF-R6 exhaust",
    "Yamaha YZF-R6 spark plugs",
 
    # ── Yamaha YZF-R1 ──
    "Yamaha YZF-R1 brake pads",
    "Yamaha YZF-R1 chain sprocket kit",
    "Yamaha YZF-R1 oil filter",
    "Yamaha YZF-R1 exhaust",
    "Yamaha YZF-R1 fairing",
 
    # ── Yamaha MT-07 ──
    "Yamaha MT-07 brake pads",
    "Yamaha MT-07 oil filter",
    "Yamaha MT-07 exhaust",
    "Yamaha MT-07 chain kit",
 
    # ── Yamaha MT-09 ──
    "Yamaha MT-09 brake pads",
    "Yamaha MT-09 oil filter",
    "Yamaha MT-09 exhaust",
 
    # ── Honda CBR600RR ──
    "Honda CBR600RR brake pads",
    "Honda CBR600RR chain sprocket",
    "Honda CBR600RR oil filter",
    "Honda CBR600RR fairing",
    "Honda CBR600RR exhaust",
 
    # ── Honda CBR1000RR ──
    "Honda CBR1000RR brake pads",
    "Honda CBR1000RR chain sprocket kit",
    "Honda CBR1000RR oil filter",
    "Honda CBR1000RR exhaust",
    "Honda CBR1000RR fairing",
 
    # ── Honda CB500F ──
    "Honda CB500F brake pads",
    "Honda CB500F oil filter",
    "Honda CB500F exhaust",
    "Honda CB500F chain kit",
 
    # ── Suzuki GSX-R600 ──
    "Suzuki GSXR600 brake pads",
    "Suzuki GSXR600 chain sprocket kit",
    "Suzuki GSXR600 oil filter",
    "Suzuki GSXR600 fairing",
    "Suzuki GSXR600 exhaust",
 
    # ── Suzuki GSX-R750 ──
    "Suzuki GSXR750 brake pads",
    "Suzuki GSXR750 oil filter",
    "Suzuki GSXR750 exhaust",
 
    # ── Suzuki SV650 ──
    "Suzuki SV650 brake pads",
    "Suzuki SV650 oil filter",
    "Suzuki SV650 chain kit",
    "Suzuki SV650 exhaust",
 
    # ── Ducati Panigale V4 ──
    "Ducati Panigale V4 brake pads",
    "Ducati Panigale V4 oil filter",
    "Ducati Panigale V4 exhaust",
    "Ducati Panigale V4 chain kit",
 
    # ── Ducati Monster ──
    "Ducati Monster brake pads",
    "Ducati Monster oil filter",
    "Ducati Monster exhaust",
 
    # ── Triumph Street Triple ──
    "Triumph Street Triple brake pads",
    "Triumph Street Triple oil filter",
    "Triumph Street Triple exhaust",
    "Triumph Street Triple chain kit",
 
    # ── Triumph Bonneville ──
    "Triumph Bonneville brake pads",
    "Triumph Bonneville oil filter",
    "Triumph Bonneville exhaust",
 
    # ── KTM Duke 390 ──
    "KTM Duke 390 brake pads",
    "KTM Duke 390 oil filter",
    "KTM Duke 390 exhaust",
    "KTM Duke 390 chain kit",
 
    # ── BMW S1000RR ──
    "BMW S1000RR brake pads",
    "BMW S1000RR oil filter",
    "BMW S1000RR exhaust",
    "BMW S1000RR chain kit",
 
    # ── Harley Davidson Sportster ──
    "Harley Davidson Sportster brake pads",
    "Harley Davidson Sportster oil filter",
    "Harley Davidson Sportster exhaust",
 
    # ── Ford Mustang ──
    "Ford Mustang brake pads",
    "Ford Mustang air filter",
    "Ford Mustang exhaust",
    "Ford Mustang spark plugs",
 
    # ── Ford Focus ──
    "Ford Focus brake pads",
    "Ford Focus air filter",
    "Ford Focus oil filter",
 
    # ── BMW 3 Series ──
    "BMW 3 Series brake pads",
    "BMW 3 Series oil filter",
    "BMW 3 Series air filter",
    "BMW 3 Series spark plugs",
 
    # ── Toyota Corolla ──
    "Toyota Corolla brake pads",
    "Toyota Corolla oil filter",
    "Toyota Corolla air filter",
 
    # ── Audi A4 ──
    "Audi A4 brake pads",
    "Audi A4 oil filter",
    "Audi A4 air filter",
 
    # ── Volkswagen Golf ──
    "Volkswagen Golf brake pads",
    "Volkswagen Golf oil filter",
    "Volkswagen Golf spark plugs",
]

# Set behaviour of API and Crawler

MAX_RESULTS_PER_PAGE = 50      # Brwose API max is 200
MAX_PAGES = 3 
SLEEP_BETWEEN_CALLS = 1.0       # 1 second sleep between requests
# CATEGORY_ID = "6000"            # eBay Motors Category



# 2) Setup of the Crawler

# check existence of data ((and log??)) folders
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("=== eBay Finding API crawler started ===")


# 3) Authentication of token function.

from requests.auth import HTTPBasicAuth

# get new token or refresh an OAuth token
def get_access_token():
    # if still valid, refresh
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            if token_data["expires_at"] > time.time():
                return token_data["access_token"]
            
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    res = requests.post(
        OAUTH_URL,
        headers=headers,
        data=data,
        auth=HTTPBasicAuth(CLIENT_ID.strip(), CLIENT_SECRET.strip()),
        timeout=30
    )

    if res.status_code != 200:
        print("OAuth error:", res.status_code, res.text)

    res.raise_for_status()
    result = res.json()

    access_token = result["access_token"]
    expires_at = time.time() + result["expires_in"] - 60    # buffer

    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": access_token, "expires_at": expires_at}, f)

    return access_token



# 4) Helper functions for the crawler to find info from website

# get a single page of results for the given keyword
def fetch_page(keyword: str, offset: int, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }
    params = {
        "q": keyword,
        "limit": MAX_RESULTS_PER_PAGE,
        "offset": offset
    }
    
    try:
        req = requests.get(API_URL, headers=headers, params=params, timeout=10)
        req.raise_for_status()
        data = req.json().get("itemSummaries", [])

        print(f"Query: {keyword}, Offset: {offset}, Items: {len(data)}")

        return data
    except Exception as e:
        logging.error(f"Error fetching {keyword} offset {offset}: {e}")
        return []

# get the relevant fields from each listing
def extract_fields(item: dict):
    try:
        return{
            "listing_id": item.get("itemId"),
            "title": item.get("title"),
            "price": item.get("price", {}).get("value"),
            "currency": item.get("price", {}).get("currency"),
            "condition": item.get("condition"),
            "brand": item.get("brand"),
            "category": item.get("categoryPath"),
            "url": item.get("itemWebUrl"),
            "seller": item.get("seller", {}).get("username"),
            "seller_rating": item.get("seller", {}).get("feedbackPercentage"),
            "location": item.get("itemLocation", {}).get("city"),
        }
    except Exception as e:
        logging.warning(f"Could not parse item: {e}")
        return None


# 5) Main Crawler function

# uses helper functions to act as main overall crawler function
def run_crawler():
    token = get_access_token()
    all_items = []
    start_time = datetime.now()

    for term in SEARCH_TERMS:
        logging.info(f"Fetching lisitngs for the term: {term}")
        print(f"Searching: {term}")

        for page in range(MAX_PAGES):
            offset = page * MAX_RESULTS_PER_PAGE
            results = fetch_page(term, offset, token)

            # no results found for that term for that page, so go to next page
            if not results:
                break

            # stop paging when getting fewer than MAX_RESULTS_PER_PAGE
            if len(results) < MAX_RESULTS_PER_PAGE:
                break

            # if results exist, extract each field by parsing page
            for item in results:
                parsed = extract_fields(item)
                if parsed:
                    # add key of term to list of other fields to identify easily
                    parsed["search_term"] = term

                    # NLP integration
                    parsed["compatibility"] = extract_compatibility(parsed.get("title", ""), index)
                    parsed["category"] = classify_category(parsed.get("title", ""))

                    all_items.append(parsed)
            
            logging.info(f"{term} | Page {page+1} | {len(results)} items fetched")
            time.sleep(SLEEP_BETWEEN_CALLS)

    # then save the results of crawler fetching and extracting results of all the search terms
    filename = os.path.join(DATA_DIR, f"listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json") 
    with open(filename, "w", encoding="utf-8") as f:json.dump(all_items, f, indent=2)

    duration = (datetime.now() - start_time).seconds
    logging.info(f"Crawl is complete: {len(all_items)} in {duration}s")
    print(f"Saved {len(all_items)} listings to {filename}")



# 6) Starting point of crawler - where the crawler is called from

if __name__ == "__main__":
    run_crawler()
