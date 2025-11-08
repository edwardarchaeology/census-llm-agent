# 🧪 Running Tests

## Quick Start

### Method 1: Using Test Runner (Easiest)

```powershell
# Show available tests
.\run_tests.bat

# Run specific test
.\run_tests.bat geography     # Test geography resolution
.\run_tests.bat multiagent    # Test multi-agent system
.\run_tests.bat basic         # Test basic functionality

# Run all tests
.\run_tests.bat all
```

### Method 2: Direct Python (Manual)

**Important:** Use the virtual environment Python!

```powershell
# Run individual tests
.\.venv\Scripts\python.exe tests\test_geography.py
.\.venv\Scripts\python.exe tests\test_multiagent.py
.\.venv\Scripts\python.exe tests\test_basic.py
```

### Method 3: Using Pytest (if installed)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

## 📋 Available Test Files

### Core Tests

- **test_multiagent.py** - Multi-agent system (5 comprehensive queries)
- **test_geography.py** - Geography resolution (parishes & cities)
- **test_basic.py** - Basic functionality
- **test_query.py** - Query execution

### Component Tests

- **test_intent.py** - Intent extraction
- **test_resolver.py** - Variable resolution
- **test_caddo_fix.py** - Specific bug fixes
- **test_comprehensive.py** - End-to-end tests
- **test_pipeline.py** - Full pipeline tests

## 🎯 Recommended Test Order

### 1. Quick Smoke Test (30 seconds)

```powershell
# Test basic functionality first
python tests\test_geography.py
```

### 2. Single-Agent Test (1-2 minutes)

```powershell
# Test single-agent mode
python tests\test_basic.py
```

### 3. Multi-Agent Test (2-3 minutes)

```powershell
# Most comprehensive test
python tests\test_multiagent.py
```

## 📊 Test Output

### Successful Test Output

```
================================================================================
TESTING MULTI-AGENT SYSTEM
================================================================================

Test 1/5: What are the top 5 census tracts in Caddo Parish by poverty rate?
--------------------------------------------------------------------------------
>>> Processing query through multi-agent system...
>>> Geography: Caddo Parish (FIPS: 017) (confidence: 0.95)
>>> Variable: B17001_002E - Poverty rate (confidence: 0.92)
>>> Task: top, Limit: 5

GEOID          tract_name                  value
22017030600    Census Tract 306            45.8%
22017030700    Census Tract 307            42.1%
...

[PASS] Query executed successfully
================================================================================
```

### Failed Test Output

```
[FAIL] Error: Could not resolve geography
Traceback (most recent call last):
  ...
```

## 🔧 Troubleshooting

### Issue: ModuleNotFoundError

**Problem:**

```
ModuleNotFoundError: No module named 'mvp_multiagent'
```

**Solution:**
The tests use `conftest.py` which automatically adds `src/` to the path. Make sure you're running tests from the project root:

```powershell
# From project root
cd "c:\Users\C00607628\OneDrive - University of Louisiana at Lafayette\Documents\github_repos\acs_llm_agent"
python tests\test_multiagent.py
```

### Issue: Ollama Not Running

**Problem:**

```
RuntimeError: Ollama API call failed: Connection refused
```

**Solution:**

```powershell
# Check if Ollama is running
ollama ps

# If not running, start it
ollama serve

# In another terminal, pull the model
ollama pull phi3:mini
```

### Issue: Missing Dependencies

**Problem:**

```
ModuleNotFoundError: No module named 'shapefile'
```

**Solution:**

```powershell
# Install all dependencies
pip install -r requirements.txt

# Or specific packages
pip install pyshp pandas requests pydantic rapidfuzz
```

### Issue: Census API Key

**Problem:**

```
Census API error: Invalid API key
```

**Solution:**

```powershell
# Set your Census API key
$env:CENSUS_API_KEY = "your_key_here"

# Or add to .env file
echo "CENSUS_API_KEY=your_key_here" > .env
```

## 📝 Writing New Tests

### Test Template

```python
"""
Test description.
"""
import sys
import os

# Path setup (automatic via conftest.py if using pytest)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mvp_multiagent import run_multiagent_query, print_result

def test_my_feature():
    """Test my specific feature."""
    query = "Your test query here"
    result = run_multiagent_query(query, verbose=False)

    # Assertions
    assert result is not None
    assert len(result) > 0
    assert "value" in result.columns

    print(f"[PASS] Test passed with {len(result)} results")

if __name__ == "__main__":
    test_my_feature()
```

### Add to Test Suite

1. Create `tests/test_myfeature.py`
2. Follow the template above
3. Run with `python tests\test_myfeature.py`

## 🎛️ Test Configuration

### Environment Variables

```powershell
# Set Ollama endpoint (if not default)
$env:OLLAMA_ENDPOINT = "http://localhost:11434"

# Set model (if not phi3:mini)
$env:OLLAMA_MODEL = "llama3.2:3b"

# Set Census API key
$env:CENSUS_API_KEY = "your_key_here"

# Set agent mode for main.py tests
$env:AGENT_MODE = "multi"
```

### Test Data Location

Tests use cached data in `cache/` directory:

- `cache/census_variables.json` - Variable catalog
- `cache/acs_*.csv` - ACS data
- `cache/tract_areas_*.csv` - Tract areas

**Clear cache:**

```powershell
Remove-Item cache\* -Recurse
```

## 📈 Performance Benchmarks

| Test                  | Duration | Queries      |
| --------------------- | -------- | ------------ |
| test_geography.py     | ~5 sec   | N/A (no LLM) |
| test_basic.py         | ~30 sec  | 3-5 queries  |
| test_multiagent.py    | ~2-3 min | 5 queries    |
| test_comprehensive.py | ~5 min   | 10+ queries  |
| **Full suite**        | ~10 min  | All tests    |

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## 📚 Related Documentation

- **docs/VERIFICATION_GUIDE.md** - Manual verification procedures
- **scripts/verify\_\*.py** - Verification scripts
- **docs/README.md** - Full project documentation

## ✅ Quick Test Checklist

Before committing code:

- [ ] `python tests\test_geography.py` - Geography resolution works
- [ ] `python tests\test_multiagent.py` - Multi-agent system works
- [ ] `python main.py --compare` - CLI works
- [ ] All tests pass without errors
- [ ] No new warnings or deprecations

---

**Need help?** Check the test output carefully - it usually tells you exactly what went wrong!
