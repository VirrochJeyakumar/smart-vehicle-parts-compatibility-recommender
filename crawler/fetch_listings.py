"""
Weeks 3-4: Implement Crawler to fetch listings using eBay's Finder API.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta



# 1) Configure the crawler with eBay Devloper Program details.

CLIENT_ID = "***REMOVED***"
CLIENT_SECRET = "***REMOVED***"

API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"

TOKEN_FILE = "token.json"
DATA_DIR = "data"
LOG_FILE = "logs/crawler.log"

# example search terms
SEARCH_TERMS = [
    "Kawasaki Ninja 650 fairing kit",
    "Yamaha R6 brake pads",
    "BMW 3 Series G20 oil filter"
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

# get new token or refresh an OAuth token
def get_access_token():
    # if still valid, refresh
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            if token_data["expires_at"] > time.time():
                return token_data["access_token"]
            
    # otherwise, fetch new token
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope/buy.browse"
    }

    res = requests.post(OAUTH_URL, headers=headers, data=data, auth=auth)
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
        "Content-Type": "application/json"
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

            # if results exist, extract each field by parsing page
            for item in results:
                parsed = extract_fields(item)
                if parsed:
                    # add key of term to list of other fields to identify easily
                    parsed["search_term"] = term
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
