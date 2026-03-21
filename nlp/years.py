# Aim of this section is 4) Year Detection

# Take the list ["kawasaki", "zx6r", "07-12"] and extract the year range
# of compatibility

# Some years are singular, some range, some have multiple ranges

# Should give a start to end range for all, even if multiple ranges, then
# a list of ranges

# Out of range years are ignored, i.e. outside 1950 to 2050

# E.g. ["kawasaki", "zx6r", "07-12"] gives [(2007, 2012)]

import re
from typing import List, Dict, Tuple, Set, Optional

def convert_year(y: str) -> int:
    n = int(y)
    # 2000 to 2030
    if n <= 30:
        return 2000 + n
    # 1931 to 1999
    else:
        return 1900 + n
    
def extract_year_ranges(text: str) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []

    # Case 1: full ranges like 2007-2012
    for a, b in re.findall(r"\b(19\d{2}|20\d{2})\s*[-/]\s*(19\d{2}|20\d{2})\b", text):
        ranges.append((int(a), int(b)))

    # Case 2: short ranges like 07-12
    for a, b in re.findall(r"\b(\d{2})\s*[-/]\s*(\d{2})\b", text):
        ranges.append((convert_year(a), convert_year(b)))

    # Case 3: long standalone years like 2007
    singles: list[int] = []

    for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text):
        singles.append(int(y))

    # Case 4: short standalone years like 08
    for y in re.findall(r"\b(\d{2})\b", text):
        # make sure duplicating ones already inside ranges
        # NOT NEEDED CASE 3 AS WELL???
        if not any(start <= convert_year(y) <= end for start, end in ranges):
            singles.append(convert_year(y))

    if singles:
        singles = sorted(set(singles))
        if len(singles) == 1:
            ranges.append((singles[0], singles[0]))
        else:
            ranges.append((singles[0], singles[-1]))
            ##### check meaning

    # remove out of range years and normalise such that start <= end
    cleaned: list[tuple[int, int]] = [] ###### check
    for start, end in ranges:
        if start > end:
            start, end = end, start
        if 1950 <= start <= 2050 and 1950 <= end <= 2050:
            cleaned.append((start, end))

    # remove duplicate ranges
    cleaned = sorted(set(cleaned))
    
    return cleaned
    