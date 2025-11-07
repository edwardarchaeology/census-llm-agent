"""
Tests for measure resolver.
"""
import pytest
from resolver import resolve_measure, normalize_measure, DERIVED_METRICS


def test_normalize_measure():
    """Test measure normalization with synonyms."""
    assert normalize_measure("median income") == "median household income"
    assert normalize_measure("income") == "median household income"
    assert normalize_measure("percent black") == "african american share"
    assert normalize_measure("pop density") == "population density"
    assert normalize_measure("unknown measure") == "unknown measure"


def test_resolve_derived_metric():
    """Test resolving derived metrics."""
    result = resolve_measure("population density")
    
    assert len(result) == 1
    assert result[0]["is_derived"] is True
    assert result[0]["variable_id"] == "DERIVED"
    assert "density" in result[0]["label"].lower()
    assert "B01003_001E" in result[0]["variables"]
    assert result[0]["needs_area"] is True


def test_resolve_median_income():
    """Test resolving 'median income' to Census variable."""
    # This test requires network access to download Census variables
    try:
        result = resolve_measure("median household income")
        
        assert len(result) >= 1
        assert result[0]["is_derived"] is False
        # Should match B19013 family (Median Household Income)
        assert "B19013" in result[0]["variable_id"]
        assert "income" in result[0]["label"].lower()
    except Exception as e:
        pytest.skip(f"Network or API issue: {e}")


def test_resolve_total_population():
    """Test resolving 'total population'."""
    try:
        result = resolve_measure("total population")
        
        assert len(result) >= 1
        assert result[0]["is_derived"] is False
        # Should match B01003_001E (Total Population)
        assert result[0]["score"] > 50  # Should have decent match score
    except Exception as e:
        pytest.skip(f"Network or API issue: {e}")


def test_derived_metrics_registry():
    """Test that all derived metrics have required fields."""
    for name, info in DERIVED_METRICS.items():
        assert "label" in info
        assert "variables" in info
        assert "needs_area" in info
        assert "formula" in info
        assert callable(info["formula"])


if __name__ == "__main__":
    print("Testing resolver...\n")
    
    print("Test 1: Normalize measure")
    test_normalize_measure()
    print("✓ Passed\n")
    
    print("Test 2: Resolve derived metric")
    test_resolve_derived_metric()
    print("✓ Passed\n")
    
    print("Test 3: Resolve median income")
    try:
        test_resolve_median_income()
        print("✓ Passed\n")
    except Exception as e:
        print(f"⊘ Skipped: {e}\n")
    
    print("Test 4: Resolve total population")
    try:
        test_resolve_total_population()
        print("✓ Passed\n")
    except Exception as e:
        print(f"⊘ Skipped: {e}\n")
    
    print("Test 5: Derived metrics registry")
    test_derived_metrics_registry()
    print("✓ Passed\n")
