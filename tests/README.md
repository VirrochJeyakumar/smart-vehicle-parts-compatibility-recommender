What is the tests folder?

An automated test suite for the project.

How to setup for testing?

pip install pytest

How to run all tests?

python -m pytest tests/ -v

How to run a specific test file?

python -m pytest tests/test_unit.py -v
python -m pytest tests/test_regression.py -v
python -m pytest tests/test_integration.py -v

Structure of tests

test_unit.py - unit tests for each extraction pipeline stage in isolation, covering text normalisation, tokenisation, make detection, model detection, year-range extraction, candidate construction, validation against the vehicle registry, and category classification.

test_regression.py - regression tests using the vehicle registry. Ensures that previously handled titles continue to extract correctly as new patterns are added. Covers standard titles, model name variations, fail-fast rejection behaviour, year-range edge cases, and pipeline determinism.

test_integration.py - integration tests verifying end-to-end data flow. Traces a single title through all seven pipeline stages, simulates the full listing record enrichment process, and verifies batch processing produces no cross-contamination between titles.
