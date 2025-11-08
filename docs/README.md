# Louisiana Census Data Getter

A natural-language interface to Louisiana census tract data, powered by Ollama and the Census API.

**Now with dual architecture**: Choose between single-agent (fast) or multi-agent (accurate) modes!

## Features

- 🗣️ **Natural language queries**: Ask questions in plain English
- 🏛️ **Complete Louisiana coverage**: All 64 parishes and major cities
- 🤖 **Dual architecture**: Single-agent (fast) or multi-agent (accurate)
- 📊 **Rich data**: ACS 5-Year estimates + derived metrics
- 🎯 **Confidence scoring**: Know when the system is uncertain (multi-agent mode)
- 💬 **Conversation memory**: Follow-up questions supported (multi-agent mode)
- 🚀 **Smart caching**: Repeats don't refetch data

## Architecture Modes

### Quick Comparison

```bash
# See detailed comparison
python main.py --compare
```

### Single-Agent Mode (Default - Fast)

- ⚡ **2-5 seconds** per query
- 🎯 One LLM call
- 💾 ~2GB memory
- ✅ Good for simple queries

### Multi-Agent Mode (Accurate)

- 🎯 **+30-50% better accuracy**
- 🤖 4 specialized agents
- 📊 Confidence scores
- 💬 Conversation context
- 💾 ~2GB memory (shared)
- ⏱️ 8-15 seconds per query

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

### Unified Interface (Recommended)

```powershell
# Single-agent mode (default - fast)
.venv\Scripts\python.exe main.py

# Multi-agent mode (more accurate)
.venv\Scripts\python.exe main.py --mode multi

# Compare architectures
.venv\Scripts\python.exe main.py --compare
```

### Direct Access (Alternative)

```powershell
# Single-agent
.venv\Scripts\python.exe mvp.py

# Multi-agent
.venv\Scripts\python.exe mvp_multiagent.py
```

### Example Queries

Try these with either mode:

- `What are the top 5 census tracts in Caddo Parish by poverty rate?`
- `Show me tracts in Lafayette with income over $75,000`
- `Find the densest populated areas in New Orleans`
- `Give me all tracts with 50% or more African Americans in Shreveport`
- `Median income between 40k and 75k in St. Tammany Parish`

**Supported Geography**: All 64 Louisiana parishes including:

- Orleans (New Orleans), Caddo (Shreveport), East Baton Rouge (Baton Rouge)
- Lafayette, Ouachita (Monroe), Calcasieu (Lake Charles), St. Tammany, Jefferson
- And 56 more parishes!

Type `quit` or `exit` to stop.

## Environment Variables

- `AGENT_MODE`: Architecture mode (`single` or `multi`)
- `OLLAMA_MODEL`: Ollama model to use (default: `phi3:mini`)
- `OLLAMA_ENDPOINT`: Ollama API endpoint (default: `http://localhost:11434`)
- `CENSUS_KEY`: Census API key (optional)

**Multi-agent specific**:

- `ORCHESTRATOR_MODEL`: Model for orchestrator (default: `phi3:mini`)
- `GEOGRAPHY_MODEL`: Model for geography agent (default: `phi3:mini`)
- `VARIABLE_MODEL`: Model for variable agent (default: `phi3:mini`)
- `PLANNER_MODEL`: Model for planner agent (default: `phi3:mini`)

## Architecture

### Single-Agent (mvp.py)

- `intent.py`: Ollama-powered intent extraction from natural language
- `resolver.py`: Census variable resolution with fuzzy matching + derived metrics
- `acs_tools.py`: ACS and TIGER/Line data fetching with caching
- `geography.py`: Louisiana parish and city mappings

### Multi-Agent (mvp_multiagent.py)

- `agents/orchestrator_agent.py`: Main coordinator with conversation memory
- `agents/geography_agent.py`: Louisiana geography specialist (64 parishes)
- `agents/variable_agent.py`: Census variable matcher with confidence scoring
- `agents/query_planner_agent.py`: Complex query decomposition
- `agents/base_agent.py`: Base agent class with Ollama integration
- `agents/config.py`: Agent configuration

### Unified Interface

- `main.py`: Configurable entry point for both architectures

### Testing

- `test_multiagent.py`: Multi-agent system tests
- `test_geography.py`: Geography coverage tests
- `verify_raw_data.py`: Data accuracy verification

## Data Sources

- **ACS 5-Year Estimates** (default: 2023) - Census Bureau
- **TIGER/Line Shapefiles** (vintage: 2024) - for tract areas

## License

MIT
