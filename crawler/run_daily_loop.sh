#!/bin/bash

while true
do
    echo "<--- Starting daily run: $(date) --->"
    cd /dcs/23/u5514423/cs310/smart-vehicle-parts-compatibility-recommender || exit 1
    /usr/bin/python3 /dcs/23/u5514423/cs310/smart-vehicle-parts-compatibility-recommender/crawler/daily_runner.py
    echo "<--- Run complete: $(date) --->"
    sleep 86400     # 24 hrs
done