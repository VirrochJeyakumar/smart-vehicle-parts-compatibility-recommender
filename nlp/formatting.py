# Aim of this section is 8) Formatting The Output

# Have a set format to return the output of each listing and list of compatibile
# candidates, each with a confidence score

from typing import List, Dict, Tuple, Set, Optional

def format_output(listing: Dict, compatible: List[Dict]) -> Dict:
    # listing = raw lisitng info from crawler
    # compatible = list of validated compatibility tuples (with confidence scores)
    return {
        "item_id": listing.get("item_id"),
        "title": listing.get("title"),
        "price": listing.get("price"),
        "currency": listing.get("currency"),
        "seller_rating": listing.get("seller_rating"),
        "url": listing.get("url"),
        "compatibility": compatible
    }