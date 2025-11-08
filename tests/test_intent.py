"""
Tests for intent extraction.
"""
import sys
import os
import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'single_agent'))

from intent import extract_intent, normalize_value, extract_city_county


def test_normalize_value():
    """Test value normalization."""
    assert normalize_value("20%") == 0.2
    assert normalize_value("35k") == 35000
    assert normalize_value("1.5m") == 1500000
    assert normalize_value("ten") == 10
    assert normalize_value("100") == 100


def test_extract_city_county():
    """Test city to county FIPS extraction."""
    assert extract_city_county("highest median income in New Orleans") == "071"
    assert extract_city_county("poverty rate in Baton Rouge") == "033"
    assert extract_city_county("density in Lafayette") == "055"
    assert extract_city_county("statewide query") is None


@pytest.mark.skipif(True, reason="Requires Ollama running - manual test only")
def test_intent_top_with_city():
    """Test: 'highest median income in New Orleans' -> task=top, limit=1, county 071."""
    intent = extract_intent("What tract has the highest median income in New Orleans?")
    
    assert intent.task == "top"
    assert "income" in intent.measure.lower()
    assert intent.limit == 1
    assert intent.sort == "desc"
    assert intent.geography.county_fips == "071"


@pytest.mark.skipif(True, reason="Requires Ollama running - manual test only")
def test_intent_filter_percentage():
    """Test: '20% or more African Americans' -> task=filter, value=0.2."""
    intent = extract_intent("Give me all tracts with 20% or more African Americans")
    
    assert intent.task == "filter"
    assert "african" in intent.measure.lower() or "black" in intent.measure.lower()
    assert intent.op == ">="
    # Value should be normalized to decimal
    assert intent.value == pytest.approx(0.2, rel=0.01) or intent.value == pytest.approx(20, rel=1)


@pytest.mark.skipif(True, reason="Requires Ollama running - manual test only")
def test_intent_range():
    """Test: 'between 40k and 75k' -> task=range, range parsed to numbers."""
    intent = extract_intent("median income between 40k and 75k")
    
    assert intent.task == "range"
    assert "income" in intent.measure.lower()
    assert intent.range_min == pytest.approx(40000, rel=0.01)
    assert intent.range_max == pytest.approx(75000, rel=0.01)


@pytest.mark.skipif(True, reason="Requires Ollama running - manual test only")
def test_intent_bottom():
    """Test: 'lowest 5 poverty rate tracts in Lafayette' -> task=bottom, limit=5."""
    intent = extract_intent("lowest 5 poverty rate tracts in Lafayette")
    
    assert intent.task == "bottom"
    assert "poverty" in intent.measure.lower()
    assert intent.limit == 5
    assert intent.sort == "asc"
    assert intent.geography.county_fips == "055"


if __name__ == "__main__":
    # Run manual tests if Ollama is available
    print("Testing intent extraction (requires Ollama)...\n")
    
    try:
        print("Test 1: Top with city")
        test_intent_top_with_city()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    try:
        print("Test 2: Filter with percentage")
        test_intent_filter_percentage()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    try:
        print("Test 3: Range query")
        test_intent_range()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    try:
        print("Test 4: Bottom query")
        test_intent_bottom()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
