# Installation & Quick Start Guide

## ✅ Setup Complete!

All dependencies have been installed and basic functionality has been tested successfully.

## What's Working

- ✅ Census variable resolver with fuzzy matching
- ✅ ACS 5-Year data fetching for Louisiana tracts
- ✅ TIGER/Line tract areas computation (pure Python, no GDAL required!)
- ✅ Derived metrics (population density, poverty rate, demographic shares)
- ✅ Data caching for fast repeated queries

## Next Steps

### 1. Start Ollama

Open a **new PowerShell terminal** and run:

```powershell
ollama serve
```

Keep this terminal open while using the app.

### 2. Pull the Model (one-time setup)

In another terminal:

```powershell
ollama pull phi3:mini
```

### 3. Run the Application

In your project terminal:

```powershell
.venv\Scripts\python.exe mvp.py
```

## Example Queries to Try

Once the app is running, try these natural language questions:

1. **Top query with city filter:**

   ```
   What tract has the highest median income in New Orleans?
   ```

2. **Filter with percentage:**

   ```
   Give me all tracts with 20% or more African Americans
   ```

3. **Top N with derived metric:**

   ```
   Show me the top 10 highest population density tracts
   ```

4. **Range query:**

   ```
   Find tracts with median income between 40k and 75k in Lafayette
   ```

5. **Filter with comparison:**
   ```
   Show me tracts with poverty rate under 15% in Baton Rouge
   ```

## Troubleshooting

### If Ollama connection fails:

- Make sure `ollama serve` is running in another terminal
- Check that the endpoint is correct: `http://localhost:11434`
- Verify the model is pulled: `ollama list`

### If Census API is slow:

- Get a free API key from: https://api.census.gov/data/key_signup.html
- Set it in PowerShell: `$env:CENSUS_KEY="YOUR_KEY"`

### If you see import errors:

- Make sure you're using the virtual environment: `.venv\Scripts\python.exe`
- Reinstall if needed: `uv pip install pandas requests pydantic rapidfuzz pyshp`

## Project Structure

```
acs_llm_agent/
├── mvp.py              # Main CLI application
├── intent.py           # Ollama-powered intent extraction
├── resolver.py         # Census variable resolver
├── acs_tools.py        # Data fetching & caching
├── test_basic.py       # Basic functionality tests
├── requirements.txt    # Dependencies (simplified, no GDAL!)
└── cache/              # Cached Census and TIGER data
```

## Technical Notes

### Dependencies Simplified

Originally required `geopandas`, `pyogrio`, and `shapely` which need GDAL (complex Windows build).

Now uses:

- `pyshp` - Pure Python shapefile reader
- Custom spherical area calculation
- No C dependencies required!

### Caching Strategy

- **Census variables**: 14-day TTL (rarely change)
- **ACS data**: Permanent cache by year/county/variables
- **TIGER areas**: Permanent cache by vintage

First query may take 30-60 seconds. Subsequent queries are instant!

## Environment Variables

Optional configurations:

```powershell
$env:OLLAMA_MODEL="phi3:mini"                    # LLM model
$env:OLLAMA_ENDPOINT="http://localhost:11434"   # Ollama API
$env:CENSUS_KEY="YOUR_KEY"                       # Census API key
```

---

**Ready to use! Start Ollama and run the app.** 🚀
