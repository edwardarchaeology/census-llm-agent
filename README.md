# MVP LLM Census Data Getter

A natural-language interface to Louisiana census tract data, powered by Ollama and the Census API.

## Features

- **Natural language queries**: Ask questions in plain English
- **Louisiana focus**: Queries limited to Louisiana census tracts (state FIPS 22)
- **City shortcuts**: Automatic county mapping for New Orleans (071), Baton Rouge (033), Lafayette (055)
- **Flexible query types**:
  - Top/bottom: "What tract has the highest median income in New Orleans?"
  - Filter: "Give me all tracts with 20% or more African Americans"
  - Range: "median income between 40k and 75k"
- **Derived metrics**: Population density, poverty rate, demographic shares
- **Smart caching**: Repeats don't refetch data

## Requirements

- Python 3.9+
- Ollama running locally with phi3:mini model
- No GDAL or complex geospatial dependencies required!

## Setup

### Quick Check (Already Installed? Start Here!)

```powershell
# Check if Ollama is ready
.venv\Scripts\python.exe check_ollama.py

# If ready, run the app
.venv\Scripts\python.exe mvp.py
```

### Full Setup (First Time)

1. **Install and start Ollama**:

```bash
# Install from: https://ollama.ai/download
ollama serve          # In a separate terminal
ollama pull phi3:mini
```

2. **Install Python dependencies**:

```powershell
# Using uv (recommended)
uv pip install pandas requests pydantic rapidfuzz pyshp

# Or using pip
pip install -r requirements.txt
```

3. **Optional: Set Census API key** (improves reliability):

```powershell
$env:CENSUS_KEY="YOUR_KEY"  # Windows PowerShell
# Get free key: https://api.census.gov/data/key_signup.html
```

## Usage

Run the interactive CLI:

```powershell
.venv\Scripts\python.exe mvp.py
```

Try these example queries:

- `What tract has the highest median income in New Orleans?`
- `Please give me all tracts with 20% or more African Americans`
- `Give me the top 10 highest population density tracts`
- `Show me tracts with poverty rate under 15% in Baton Rouge`
- `Find tracts with median income between 40k and 75k in Lafayette`

Type `quit` or `exit` to stop.

## Environment Variables

- `OLLAMA_MODEL`: Ollama model to use (default: `phi3:mini`)
- `OLLAMA_ENDPOINT`: Ollama API endpoint (default: `http://localhost:11434`)
- `CENSUS_KEY`: Census API key (optional)

## Architecture

- `mvp.py`: CLI runner and main query orchestration
- `intent.py`: Ollama-powered intent extraction from natural language
- `resolver.py`: Census variable resolution with fuzzy matching + derived metrics
- `acs_tools.py`: ACS and TIGER/Line data fetching with caching
- `tests/`: Unit and integration tests

## Data Sources

- **ACS 5-Year Estimates** (default: 2023) - Census Bureau
- **TIGER/Line Shapefiles** (vintage: 2024) - for tract areas

## License

MIT
