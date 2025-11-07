"""
Integration tests for full pipeline.
Mark as integration tests that can be skipped if no network.
"""
import pytest
from mvp import run_query


@pytest.mark.integration
@pytest.mark.skipif(True, reason="Integration test - requires Ollama + network - manual only")
def test_pipeline_new_orleans_filter():
    """Integration test: run full query on New Orleans with filter."""
    question = "Give me tracts with median income over 50k in New Orleans"
    
    result = run_query(question)
    
    # Should have non-empty result
    assert not result.empty
    
    # Should have required columns
    assert "GEOID" in result.columns
    assert "tract_name" in result.columns
    assert "value" in result.columns
    
    # All values should be > 50000
    assert (result["value"] > 50000).all()
    
    # Should have label in attrs
    assert "label" in result.attrs


@pytest.mark.integration
@pytest.mark.skipif(True, reason="Integration test - requires Ollama + network - manual only")
def test_pipeline_top_population_density():
    """Integration test: top 5 population density tracts."""
    question = "Show me the top 5 highest population density tracts"
    
    result = run_query(question)
    
    # Should have exactly 5 rows
    assert len(result) == 5
    
    # Should be sorted in descending order
    assert result["value"].is_monotonic_decreasing


@pytest.mark.integration
@pytest.mark.skipif(True, reason="Integration test - requires Ollama + network - manual only")
def test_pipeline_range_query():
    """Integration test: range query for income."""
    question = "Find tracts with median income between 30k and 60k in Baton Rouge"
    
    result = run_query(question)
    
    # Should have non-empty result
    assert not result.empty
    
    # All values should be in range
    assert (result["value"] >= 30000).all()
    assert (result["value"] <= 60000).all()


if __name__ == "__main__":
    print("Integration tests (requires Ollama + network)...\n")
    
    try:
        print("Test 1: New Orleans filter query")
        test_pipeline_new_orleans_filter()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    try:
        print("Test 2: Top population density")
        test_pipeline_top_population_density()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    try:
        print("Test 3: Range query")
        test_pipeline_range_query()
        print("✓ Passed\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
