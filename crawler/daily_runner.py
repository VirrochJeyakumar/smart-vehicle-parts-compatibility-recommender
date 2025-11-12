"""
Daily running script that runs the fetch_listings.py crawler
once per day and automatically deletes old (over 7 days) data files
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
import logging

# paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
LOG_FILE = os.path.join(BASE_DIR, "..", "logs", "daily_runner.log")

# ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# parameters
CRAWLER_SCRIPT = os.path.join(BASE_DIR, "fetch_listings.py")
DELETE_AFTER_DAYS = 7

# method to run crawler as a subprocess
def run_crawler():
    logging.info("Starting daily crawler run...")
    print("Running eBay crawler...")
    try:
        subprocess.run(["python3", CRAWLER_SCRIPT], check=True)
        logging.info("Crawler run completed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Crawler failed with error: {e}")
        print("Crawler failed - check logs for details")


# method to delete data files older than chosen number of days
def cleanup_old_files():
    now = datetime.now()
    cutoff = now - timedelta(days=DELETE_AFTER_DAYS)
    deleted = 0

    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            path = os.path.join(DATA_DIR, file)
            modified_time = datetime.fromtimestamp(os.path.getmtime(path))
            if modified_time < cutoff:
                os.remove(path)
                logging.info(f"Deleted old file: {path}")
                deleted += 1
    
    logging.info(f"Cleanup complete - deleted {deleted} old files")
    print(f"Deleted {deleted} old JSON files")

# main method calling both other methods
def main():
    print("<--- Daily Crawler Started --->")
    run_crawler()
    cleanup_old_files()
    print("Daily run complete")

if __name__ == "__main__":
    main()