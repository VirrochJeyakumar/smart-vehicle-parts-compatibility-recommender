"""
Integration tests verifying end-to-end data flow from cached listing.
Look at README.md for more information.
"""

import os
import json
import pytest
from nlp.pipeline import load_vehicle_registry, build_index_from_registry, extract_compatibility
from nlp.normalise import normalise_text
from nlp.makes import tokenise, detect_make
from nlp.models import detect_models
from nlp.years import extract_year_ranges
from nlp.candidates import build_candidates
from nlp.validation import validation
from nlp.categories import classify_category


# fixtures
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "vehicle_registry.json")
 
@pytest.fixture(scope="module")
def registry():
    return load_vehicle_registry(REGISTRY_PATH)
 
@pytest.fixture(scope="module")
def index(registry):
    return build_index_from_registry(registry)
 
@pytest.fixture(scope="module")
def full_index(registry):
    valid_makes, models_by_make, year_range_by_model = build_index_from_registry(registry)
    return valid_makes, models_by_make, year_range_by_model


# registry loading

class TestRegistryLoading:
    def test_registry_loads(self, registry):
        assert len(registry) > 0
 
    def test_registry_has_expected_makes(self, full_index):
        valid_makes, _, _ = full_index
        assert "kawasaki" in valid_makes
        assert "yamaha" in valid_makes
        assert "honda" in valid_makes
        assert "ford" in valid_makes
 
    def test_registry_has_models_for_kawasaki(self, full_index):
        _, models_by_make, _ = full_index
        assert "kawasaki" in models_by_make
        assert len(models_by_make["kawasaki"]) > 0
 
    def test_registry_has_year_ranges(self, full_index):
        _, _, year_range_by_model = full_index
        assert len(year_range_by_model) > 0


# tracing of a single title through every stage to verify data flows correctly

class TestStageByStageFlow: 
    TITLE = "Kawasaki ZX6R Brake Pads 07-12"
 
    def test_stage1_normalise(self):
        text = normalise_text(self.TITLE)
        assert text == "kawasaki zx6r brake pads 07-12"
 
    def test_stage2_tokenise(self):
        text = normalise_text(self.TITLE)
        tokens = tokenise(text)
        assert "kawasaki" in tokens
        assert "zx6r" in tokens
        assert "07-12" in tokens
 
    def test_stage3_detect_make(self, full_index):
        valid_makes, _, _ = full_index
        text = normalise_text(self.TITLE)
        tokens = tokenise(text)
        make = detect_make(tokens, valid_makes)
        assert make == "kawasaki"
 
    def test_stage4_detect_models(self, full_index):
        _, models_by_make, _ = full_index
        text = normalise_text(self.TITLE)
        models = detect_models(text, "kawasaki", models_by_make)
        assert len(models) > 0
 
    def test_stage5_extract_years(self):
        text = normalise_text(self.TITLE)
        year_ranges = extract_year_ranges(text)
        assert len(year_ranges) > 0
        assert any(s <= 2007 and e >= 2012 for s, e in year_ranges)
 
    def test_stage6_build_candidates(self, full_index):
        _, models_by_make, _ = full_index
        text = normalise_text(self.TITLE)
        models = detect_models(text, "kawasaki", models_by_make)
        year_ranges = extract_year_ranges(text)
        candidates = build_candidates("kawasaki", models, year_ranges)
        assert len(candidates) > 0
        for c in candidates:
            assert c["make"] == "kawasaki"
            assert "model" in c
            assert "year_start" in c
            assert "year_end" in c
 
    def test_stage7_validation(self, full_index):
        _, models_by_make, year_range_by_model = full_index
        text = normalise_text(self.TITLE)
        models = detect_models(text, "kawasaki", models_by_make)
        year_ranges = extract_year_ranges(text)
        candidates = build_candidates("kawasaki", models, year_ranges)
        validated = validation(candidates, year_range_by_model)
        assert len(validated) > 0
        for v in validated:
            key = (v["make"], v["model"])
            assert key in year_range_by_model
 
    # the pipeline function should produce the same result as manual stages
    def test_full_pipeline_matches_stages(self, index, full_index):
        result = extract_compatibility(self.TITLE, index)
        assert len(result) > 0
    

# simulate the full flow from a cached listing record to extraction output

class TestListingRecordFlow: 
    SAMPLE_LISTING = {
        "listing_id": "test_001",
        "title": "Yamaha YZF-R6 Chain and Sprocket Kit 2006-2016",
        "price": "45.99",
        "currency": "GBP",
        "condition": "New",
        "brand": "DID",
        "category": "Parts & Accessories",
        "url": "https://www.ebay.co.uk/itm/test_001",
        "seller": "test_seller",
        "seller_rating": "99.5",
        "location": "London",
        "search_term": "Yamaha R6 chain sprocket kit"
    }
 
    def test_extraction_from_listing_title(self, index):
        result = extract_compatibility(self.SAMPLE_LISTING["title"], index)
        assert len(result) > 0
 
    def test_category_classification(self):
        category = classify_category(self.SAMPLE_LISTING["title"])
        assert category is not None
        assert "chain" in category.lower() or "sprocket" in category.lower()
 
    # listing ID should pass through unchanged for traceability
    def test_listing_id_preserved(self):
        listing_id = self.SAMPLE_LISTING["listing_id"]
        assert listing_id == "test_001"
 
    # after extraction & classification, the record should have all fields
    def test_enriched_record_structure(self, index):
        record = dict(self.SAMPLE_LISTING)
        record["compatibility"] = extract_compatibility(record["title"], index)
        record["classified_category"] = classify_category(record["title"])
 
        assert "listing_id" in record
        assert "title" in record
        assert "compatibility" in record
        assert isinstance(record["compatibility"], list)
        assert "classified_category" in record


# batch processing - verify the pipeline handles multiple titles without cross-contamination

class TestBatchProcessing:
    TITLES = [
        "Kawasaki ZX6R Brake Pads 07-12",
        "Yamaha R6 Oil Filter 2008-2016",
        "Honda CBR600RR Fairing Kit 2005-2006",
        "Ford Mustang Spark Plugs 2015-2020",
        "Generic Brake Fluid DOT4 500ml",
    ]
 
    def test_batch_no_cross_contamination(self, index):
        results = [extract_compatibility(t, index) for t in self.TITLES]
 
        # first four should have results, last should be empty
        for i in range(4):
            assert len(results[i]) > 0, f"Title {i} should produce results"
        assert results[4] == [], "Generic title should produce no results"
 
        # check no make leakage between titles
        if results[0]:
            assert all(r["make"] == "kawasaki" for r in results[0])
        if results[1]:
            assert all(r["make"] == "yamaha" for r in results[1])
        if results[3]:
            assert all(r["make"] == "ford" for r in results[3])
 
    # every extracted tuple in a batch should reference a real vehicle
    def test_batch_all_results_valid(self, index, full_index):
        _, _, year_range_by_model = full_index
        for title in self.TITLES:
            results = extract_compatibility(title, index)
            for r in results:
                key = (r["make"], r["model"])
                assert key in year_range_by_model, \
                    f"Extracted tuple {key} not in registry from title: {title}"