# Project Structure

```
acs_llm_agent/
│
├── main.py                      # 🚀 Main entry point with mode switching
│
├── src/                         # 📦 Source code
│   ├── single_agent/            # Single-agent implementation
│   │   ├── mvp.py              # CLI runner
│   │   ├── intent.py           # Intent extraction
│   │   └── resolver.py         # Variable resolution
│   │
│   ├── agents/                  # Multi-agent system
│   │   ├── __init__.py
│   │   ├── config.py           # Agent configurations
│   │   ├── base_agent.py       # Base agent class
│   │   ├── orchestrator_agent.py
│   │   ├── geography_agent.py
│   │   ├── variable_agent.py
│   │   └── query_planner_agent.py
│   │
│   ├── mvp_multiagent.py       # Multi-agent CLI runner
│   ├── acs_tools.py            # Census API + TIGER/Line integration
│   └── geography.py            # Louisiana geography data (64 parishes)
│
├── tests/                       # 🧪 Test suite
│   ├── test_basic.py
│   ├── test_caddo_fix.py
│   ├── test_comprehensive.py
│   ├── test_geography.py
│   ├── test_multiagent.py
│   └── test_query.py
│
├── scripts/                     # 🔧 Utility scripts
│   ├── check_ollama.py         # Check Ollama connectivity
│   ├── debug_intent.py         # Debug intent extraction
│   ├── side_by_side_verification.py
│   ├── verify_caddo_poverty.py
│   └── verify_raw_data.py
│
├── docs/                        # 📚 Documentation
│   ├── README.md               # Full documentation
│   ├── USAGE_GUIDE.md          # Usage guide with examples
│   ├── MULTIAGENT_SUMMARY.md   # Multi-agent architecture
│   ├── QUICKSTART.md           # Quick start guide
│   ├── VERIFICATION_GUIDE.md   # Testing and verification
│   ├── BUGFIX_PERCENTAGE_SCALING.md
│   └── UNICODE_FIX.md
│
├── cache/                       # 💾 Data cache
│   ├── census_variables.json   # Variable catalog cache
│   ├── acs_*.csv              # ACS data cache
│   └── tract_areas_*.csv      # Tract area cache
│
├── .venv/                       # 🐍 Python virtual environment
├── .git/                        # Git repository
├── .gitignore
├── .python-version
├── pyproject.toml              # Python project config
├── requirements.txt            # Dependencies
├── run.bat                     # Windows batch launcher
└── README.md                   # Project overview
```

## Module Responsibilities

### Single-Agent (`src/single_agent/`)

- **mvp.py**: Main orchestrator, runs queries through single LLM call
- **intent.py**: Extracts structured intent using Ollama with few-shot prompting
- **resolver.py**: Resolves measure names to Census variables using fuzzy matching

### Multi-Agent (`src/agents/`)

- **orchestrator_agent.py**: Coordinates all agents, maintains conversation history
- **geography_agent.py**: Resolves geographic entities (parishes, cities) to FIPS codes
- **variable_agent.py**: Resolves measure names to Census variables with confidence
- **query_planner_agent.py**: Plans complex multi-step queries (comparisons, aggregations)
- **base_agent.py**: Abstract base class with Ollama integration

### Shared (`src/`)

- **acs_tools.py**: Census API and TIGER/Line data fetching
- **geography.py**: Louisiana-specific geography data (64 parishes + cities)
- **mvp_multiagent.py**: Multi-agent CLI runner

## Import Structure

```python
# From root (main.py)
sys.path.insert(0, 'src/single_agent')
from mvp import main as mvp_main

sys.path.insert(0, 'src')
from mvp_multiagent import main as multiagent_main

# Within single_agent modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from single_agent.intent import extract_intent
from acs_tools import fetch_data_for_query

# Within multi-agent modules
from agents.orchestrator_agent import OrchestratorAgent
from acs_tools import fetch_data_for_query
```

## Data Flow

### Single-Agent Mode

```
User Query
    ↓
intent.py (Ollama extraction)
    ↓
resolver.py (fuzzy matching)
    ↓
acs_tools.py (Census API)
    ↓
Result DataFrame
```

### Multi-Agent Mode

```
User Query
    ↓
Orchestrator Agent
    ├→ Geography Agent (parish/city → FIPS)
    ├→ Variable Agent (measure → Census variable)
    └→ Query Planner (detect complexity)
    ↓
acs_tools.py (Census API)
    ↓
Result DataFrame (with confidence scores)
```

## Cache Strategy

1. **Variable Catalog** (`cache/census_variables.json`)

   - TTL: 14 days
   - All ACS 5-Year variables
   - ~500KB

2. **ACS Data** (`cache/acs_YYYY_STATECODE_COUNTYFIPS_VARS.csv`)

   - Per-query caching
   - Keyed by year, geography, variables
   - Persistent

3. **Tract Areas** (`cache/tract_areas_YYYY_STATECODE.csv`)
   - Per-state caching
   - From TIGER/Line shapefiles
   - Used for population density calculations
