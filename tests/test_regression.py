"""
Regression tests for previously encountered edge cases.
Look at README.md for more information.
"""

import os
import json
import pytest
from nlp.pipeline import load_vehicle_registry, build_index_from_registry, extract_compatibility


# fixtures

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "vehicle_registry.json")
 
@pytest.fixture(scope="module")
# load registry and build index once for all tests
def index():
    registry = load_vehicle_registry(REGISTRY_PATH)
    return build_index_from_registry(registry)


# helper

# check if a specific compatibility tuple is in the results
def has_tuple(results, make, model, year_start=None, year_end=None):
    for r in results:
        if r["make"] == make and r["model"] == model:
            if year_start and r["year_start"] != year_start:
                continue
            if year_end and r["year_end"] != year_end:
                continue
            return True
    return False



# standard titles

class TestStandardTitles:
    def test_standard_kawasaki_zx6r(self, index):
        result = extract_compatibility("Kawasaki ZX6R Brake Pads 07-12", index)
        assert len(result) > 0
        assert has_tuple(result, "kawasaki", "zx-6r")

    def test_standard_yamaha_r6(self, index):
        result = extract_compatibility("Yamaha YZF-R6 Oil Filter 2008-2016", index)
        assert len(result) > 0
        assert has_tuple(result, "yamaha", "yzf-r6")
 
    def test_standard_honda_cbr(self, index):
        result = extract_compatibility("Honda CBR600RR Chain Sprocket Kit 2003-2006", index)
        assert len(result) > 0
 
    def test_standard_ford_mustang(self, index):
        result = extract_compatibility("Ford Mustang Brake Pads 2015-2020", index)
        assert len(result) > 0
        assert has_tuple(result, "ford", "mustang")
 
    def test_four_digit_year_range(self, index):
        result = extract_compatibility("Kawasaki ZX-6R Fairing 2007-2012", index)
        assert len(result) > 0
 
    def test_two_digit_year_range(self, index):
        result = extract_compatibility("Kawasaki ZX-6R Fairing 07-12", index)
        assert len(result) > 0
    

# model name variations

class TestModelVariations:
    def test_hyphenated_model(self, index):
        result = extract_compatibility("Kawasaki ZX-6R Brake Pads 2010", index)
        assert len(result) > 0
 
    def test_no_hyphen_model(self, index):
        result = extract_compatibility("Kawasaki ZX6R Brake Pads 2010", index)
        assert len(result) > 0
 
    def test_space_in_model(self, index):
        result = extract_compatibility("Kawasaki ZX 6R Brake Pads 2010", index)
        assert len(result) > 0


# fail-fast rejections

class TestRejection:
    def test_no_make(self, index):
        result = extract_compatibility("Brake Pads Front Ceramic 07-12", index)
        assert result == []
 
    def test_no_model(self, index):
        result = extract_compatibility("Kawasaki Brake Pads Front Ceramic", index)
        assert result == []
 
    def test_no_year(self, index):
        result = extract_compatibility("Kawasaki ZX6R Brake Pads Front", index)
        assert result == []
 
    def test_empty_title(self, index):
        result = extract_compatibility("", index)
        assert result == []
 
    def test_none_title(self, index):
        result = extract_compatibility(None, index)
        assert result == []
 
    def test_gibberish(self, index):
        result = extract_compatibility("asdfgh jklmn 12345", index)
        assert result == []


# year-range edge cases

class TestYearEdgeCases:
    def test_single_year(self, index):
        result = extract_compatibility("Kawasaki ZX-6R Exhaust 2010", index)
        assert len(result) > 0
        assert any(r["year_start"] == r["year_end"] == 2010 for r in result)
 
    # seller claims wider range than production -> should be narrowed
    def test_overbroad_range_narrowed(self, index):
        result = extract_compatibility("Kawasaki ZX-6R Fairings 2000-2020", index)
        if len(result) > 0:
            for r in result:
                assert r["year_start"] >= 1996
                assert r["year_end"] <= 2024


# numerical ambiguity

class TestNumericAmbiguity:
    # years should be 2005-2006, not something from 600 in model
    def test_dimension_not_misread_as_year(self, index):
        result = extract_compatibility("Honda CBR600RR Brake Pads 2005-2006", index)
        if len(result) > 0:
            for r in result:
                assert r["year_start"] >= 2003


# pipeline determinism

class TestDeterminism:
    # running the same title twice must produce identical results
    def test_same_input_same_output(self, index):
        title = "Kawasaki ZX6R Chain Sprocket Kit 07-12"
        result1 = extract_compatibility(title, index)
        result2 = extract_compatibility(title, index)
        assert result1 == result2
 
    # 10 runs of the same results must all match
    def test_determinism_across_ten_runs(self, index):
        title = "Yamaha R6 Oil Filter 2008-2016"
        results = [extract_compatibility(title, index) for _ in range(10)]
        assert all(r == results[0] for r in results)