"""
Unit tests for each stage of the compatibility extraction pipeline.
Look at README.md for more information.
"""

import pytest
from nlp.normalise import normalise_text
from nlp.makes import tokenise, detect_make
from nlp.models import detect_models
from nlp.years import extract_year_ranges
from nlp.candidates import build_candidates
from nlp.validation import validation
from nlp.categories import classify_category


# text normalisation tests

class TestNormalise:
    def test_lowercase(self):
        assert normalise_text("Kawasaki ZX6R") == "kawasaki zx6r"
 
    def test_underscores_replaced(self):
        assert normalise_text("brake_pads_kit") == "brake pads kit"
 
    def test_slashes_replaced(self):
        assert normalise_text("oil/air filter") == "oil air filter"
 
    def test_pipes_replaced(self):
        assert normalise_text("front|rear brake") == "front rear brake"
 
    def test_en_dash_to_hyphen(self):
        assert normalise_text("07–12") == "07-12"
 
    def test_em_dash_to_hyphen(self):
        assert normalise_text("07—12") == "07-12"
 
    def test_multiple_spaces_collapsed(self):
        assert normalise_text("kawasaki   zx6r    07-12") == "kawasaki zx6r 07-12"
 
    def test_whitespace_trimmed(self):
        assert normalise_text("  kawasaki zx6r  ") == "kawasaki zx6r"
 
    def test_empty_string(self):
        assert normalise_text("") == ""
 
    def test_none_input(self):
        assert normalise_text(None) == ""
 
    # hyphens must stay
    def test_hyphens_preserved(self):
        assert "-" in normalise_text("ZX-6R 07-12")


# tokenisation tests

class TestTokenise:
    def test_basic_split(self):
        assert tokenise("kawasaki zx6r 07-12") == ["kawasaki", "zx6r", "07-12"]
 
    def test_single_token(self):
        assert tokenise("kawasaki") == ["kawasaki"]
 
    # hyphens should not split tokens
    def test_hyphenated_stays_together(self):
        tokens = tokenise("zx-6r 07-12")
        assert "zx-6r" in tokens
        assert "07-12" in tokens
    

# make detection tests

class TestDetectMake:
    @pytest.fixture
    def valid_makes(self):
        return {"kawasaki", "yamaha", "honda", "ford", "suzuki", "bmw"}
 
    def test_first_match(self, valid_makes):
        tokens = ["kawasaki", "zx6r", "brake", "pads"]
        assert detect_make(tokens, valid_makes) == "kawasaki"
 
    def test_make_not_first_token(self, valid_makes):
        tokens = ["brake", "pads", "honda", "cbr600rr"]
        assert detect_make(tokens, valid_makes) == "honda"
 
    def test_no_make_found(self, valid_makes):
        tokens = ["brake", "pads", "generic", "part"]
        assert detect_make(tokens, valid_makes) is None
 
    def test_empty_tokens(self, valid_makes):
        assert detect_make([], valid_makes) is None
 
    # make detection expects a normalised (lowercase) input
    def test_case_sensitive_requires_lowercase(self, valid_makes):
        tokens = ["Kawasaki", "zx6r"]
        assert detect_make(tokens, valid_makes) is None


# model detection tests

class TestDetectModels:
    @pytest.fixture
    def models_by_make(self):
        return {
            "kawasaki": {"zx-6r", "ninja 650", "z900"},
            "yamaha": {"yzf-r6", "yzf-r1", "mt-07"},
            "honda": {"cbr600rr", "cb500f"},
        }
 
    def test_exact_match(self, models_by_make):
        result = detect_models("kawasaki zx-6r brake pads", "kawasaki", models_by_make)
        assert "zx-6r" in result
 
    def test_no_hyphen_variant(self, models_by_make):
        result = detect_models("kawasaki zx6r fairings", "kawasaki", models_by_make)
        assert "zx-6r" in result
 
    def test_space_variant(self, models_by_make):
        result = detect_models("kawasaki zx 6r exhaust", "kawasaki", models_by_make)
        assert "zx-6r" in result
 
    def test_multi_word_model(self, models_by_make):
        result = detect_models("kawasaki ninja 650 chain kit", "kawasaki", models_by_make)
        assert "ninja 650" in result
 
    def test_no_model_found(self, models_by_make):
        result = detect_models("kawasaki generic brake fluid", "kawasaki", models_by_make)
        assert result == []
 
    def test_unknown_make(self, models_by_make):
        result = detect_models("ducati panigale v4", "ducati", models_by_make)
        assert result == []
 
    def test_multiple_models_detected(self, models_by_make):
        result = detect_models("yamaha yzf-r6 yzf-r1 brake pads", "yamaha", models_by_make)
        assert "yzf-r6" in result
        assert "yzf-r1" in result


# year-range tests

class TestExtractYearRanges:
    def test_full_four_digit_range(self):
        result = extract_year_ranges("fits 2007-2012 models")
        assert (2007, 2012) in result
 
    def test_abbreviated_two_digit_range(self):
        result = extract_year_ranges("fits 07-12")
        assert (2007, 2012) in result
 
    def test_standalone_four_digit_year(self):
        result = extract_year_ranges("fits 2010 model")
        assert (2010, 2010) in result
 
    def test_standalone_two_digit_year(self):
        result = extract_year_ranges("fits 08 model")
        assert (2008, 2008) in result
 
    def test_two_digit_conversion_2000s(self):
        result = extract_year_ranges("fits 00-30")
        assert (2000, 2030) in result
 
    def test_two_digit_conversion_1900s(self):
        result = extract_year_ranges("fits 95-99")
        assert (1995, 1999) in result
 
    def test_out_of_bounds_rejected(self):
        result = extract_year_ranges("fits 1920-1925")
        assert len(result) == 0
 
    def test_swapped_range_corrected(self):
        result = extract_year_ranges("fits 2012-2007")
        assert (2007, 2012) in result
 
    def test_duplicate_ranges_removed(self):
        result = extract_year_ranges("2007-2012 2007-2012")
        assert len(result) == 1
 
    def test_no_years_returns_empty(self):
        result = extract_year_ranges("brake pads ceramic front")
        assert result == []
 
    def test_slash_separator(self):
        result = extract_year_ranges("fits 07/12")
        assert (2007, 2012) in result


# candidate construction tests

class TestBuildCandidates:
    def test_single_model_single_range(self):
        result = build_candidates("kawasaki", ["zx-6r"], [(2007, 2012)])
        assert len(result) == 1
        assert result[0] == {
            "make": "kawasaki", "model": "zx-6r",
            "year_start": 2007, "year_end": 2012
        }
 
    # 2 models x 2 year-ranges
    def test_cartesian_product(self):
        result = build_candidates("kawasaki", ["zx-6r", "ninja 650"], [(2007, 2012), (2015, 2020)])
        assert len(result) == 4 
 
    def test_all_inherit_make(self):
        result = build_candidates("yamaha", ["yzf-r6", "yzf-r1"], [(2010, 2015)])
        for c in result:
            assert c["make"] == "yamaha"
 
    def test_empty_models(self):
        assert build_candidates("kawasaki", [], [(2007, 2012)]) == []
 
    def test_empty_years(self):
        assert build_candidates("kawasaki", ["zx-6r"], []) == []
 
    def test_empty_make(self):
        assert build_candidates("", ["zx-6r"], [(2007, 2012)]) == []

    
# validation (against registry) tests

class TestValdiation:
    @pytest.fixture
    def year_range_by_model(self):
        return {
            ("kawasaki", "zx-6r"): (2007, 2012),
            ("yamaha", "yzf-r6"): (2006, 2020),
            ("honda", "cbr600rr"): (2003, 2017),
        }
 
    def test_valid_candidate_passes(self, year_range_by_model):
        candidates = [{"make": "kawasaki", "model": "zx-6r", "year_start": 2007, "year_end": 2012}]
        result = validation(candidates, year_range_by_model)
        assert len(result) == 1
        assert result[0]["year_start"] == 2007
        assert result[0]["year_end"] == 2012
 
    def test_unknown_model_rejected(self, year_range_by_model):
        candidates = [{"make": "kawasaki", "model": "zzr1400", "year_start": 2007, "year_end": 2012}]
        result = validation(candidates, year_range_by_model)
        assert len(result) == 0
 
    # seller claims 2005-2015, but ZX-6R only 2007-2012
    def test_year_range_narrowed_by_intersection(self, year_range_by_model):
        candidates = [{"make": "kawasaki", "model": "zx-6r", "year_start": 2005, "year_end": 2015}]
        result = validation(candidates, year_range_by_model)
        assert len(result) == 1
        assert result[0]["year_start"] == 2007
        assert result[0]["year_end"] == 2012
 
    # seller claims 2015-2020, but ZX-6R only 2007-2012
    def test_no_overlap_rejected(self, year_range_by_model):
        candidates = [{"make": "kawasaki", "model": "zx-6r", "year_start": 2015, "year_end": 2020}]
        result = validation(candidates, year_range_by_model)
        assert len(result) == 0
 
    # seller claims 2010-2025, ZX-6R is 2007-2012 -> should narrow to 2010-2012
    def test_partial_overlap_kept(self, year_range_by_model):
        candidates = [{"make": "kawasaki", "model": "zx-6r", "year_start": 2010, "year_end": 2025}]
        result = validation(candidates, year_range_by_model)
        assert len(result) == 1
        assert result[0]["year_start"] == 2010
        assert result[0]["year_end"] == 2012
 
      # only zx-6r passes (only zx-6r model exists in registry)
    def test_multiple_candidates_filtered(self, year_range_by_model):
        candidates = [
            {"make": "kawasaki", "model": "zx-6r", "year_start": 2007, "year_end": 2012},
            {"make": "kawasaki", "model": "zzr1400", "year_start": 2007, "year_end": 2012},
        ]
        result = validation(candidates, year_range_by_model)
        assert len(result) == 1


# category classification tests

class TestClassifyCategory:
    def test_brake_pads(self):
        assert classify_category("EBC Front Brake Pads Kawasaki ZX6R") == "brake pads"
 
    def test_oil_filter(self):
        assert classify_category("HiFlo Oil Filter Honda CBR600RR") == "oil filters"
 
    def test_chain_kit(self):
        assert classify_category("DID Chain and Sprocket Kit Yamaha R6") == "chain kit"
 
    def test_no_match(self):
        assert classify_category("random motorcycle accessory item") is None
 
    def test_empty_string(self):
        assert classify_category("") is None
 
    def test_none_input(self):
        assert classify_category(None) is None