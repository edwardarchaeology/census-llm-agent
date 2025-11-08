# Project Structure

```
acs_llm_agent/
|-- main.py                 # CLI entry point
|-- src/                    # Source code
|   |-- single_agent/
|   |   |-- mvp.py          # CLI runner
|   |   |-- intent.py       # Intent extraction
|   |   `-- resolver.py     # Variable resolution
|   |-- agents/
|   |   |-- __init__.py
|   |   |-- config.py       # Agent configurations
|   |   |-- base_agent.py
|   |   |-- orchestrator_agent.py
|   |   |-- geography_agent.py
|   |   |-- variable_agent.py
|   |   `-- query_planner_agent.py
|   |-- mvp_multiagent.py   # Multi-agent CLI runner
|   |-- acs_tools.py        # Census API + TIGER/Line integration
|   `-- geography.py        # Louisiana geography data
|-- gui/                    # Streamlit app
|-- scripts/                # Utility scripts
|   |-- build_doc_index.py
|   |-- check_ollama.py
|   |-- debug_intent.py
|   |-- fetch_orleans_income.py
|   |-- run_shiny.py
|   |-- show_structure.py
|   |-- side_by_side_verification.py
|   |-- verify_caddo_poverty.py
|   |-- verify_raw_data.py
|   `-- windows/            # Windows helpers
|-- docs/
|   |-- README.md
|   |-- USAGE_GUIDE.md
|   |-- QUICKSTART.md
|   |-- MULTIAGENT_SUMMARY.md
|   |-- VERIFICATION_GUIDE.md
|   |-- BUGFIX_PERCENTAGE_SCALING.md
|   |-- UNICODE_FIX.md
|   `-- notes/
|-- acs_docs/
|-- cache/
|-- tests/
|   |-- conftest.py
|   |-- test_basic.py
|   |-- test_caddo_fix.py
|   |-- test_comprehensive.py
|   |-- test_geography.py
|   |-- test_intent.py
|   |-- test_pipeline.py
|   |-- test_query.py
|   |-- test_resolver.py
|   `-- manual/
|-- README.md
|-- requirements.txt
|-- pyproject.toml
`-- uv.lock
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
User Query -> intent.py -> resolver.py -> acs_tools.py -> Result DataFrame
```

### Multi-Agent Mode

```
User Query -> Orchestrator -> (Geography + Variable + Planner agents) -> acs_tools.py -> Result DataFrame
```

## Cache Strategy

1. **Variable Catalog** (`cache/census_variables.json`)
   - TTL: 14 days
   - All ACS 5-Year variables (~500KB)

2. **ACS Data** (`cache/acs_{year}_{state}_{county}_{vars}.csv`)
   - Per-query caching keyed by year/geography/variables
   - Persistent

3. **Tract Areas** (`cache/tract_areas_{year}_{state}.csv`)
   - Per-state TIGER/Line area data
   - Used for derived metrics like population density
