# Louisiana Census Data Agent

A dual-architecture LLM-powered agent for querying Louisiana census tract data using natural language, enhanced with **LangChain** for conversational intelligence.

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green.svg)](https://ollama.ai/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0-purple.svg)](https://python.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

### Core Capabilities

- **Dual Architecture**: Choose between fast single-agent or accurate multi-agent mode
- **Natural Language**: Ask questions in plain English
- **Louisiana Coverage**: All 64 parishes + major cities
- **Smart Resolution**: Fuzzy matching for measures and geography
- **Intelligent Caching**: Multi-layer caching for fast responses
- **Rich Metrics**: Population, income, poverty, race, age, and more
- **Clean Output**: ASCII-safe formatting for terminal display

### 🧠 LangChain Intelligence (NEW!)

- **💬 Conversational Memory**: Remember context across queries - ask follow-up questions naturally
- **📚 RAG for Variables**: Semantic search through 30,000+ Census variables for better matching
- **🔄 Follow-up Detection**: System detects and handles "Now show me...", "What about..." patterns
- **📜 Context Tracking**: Separate conversation histories for main queries and Variable Assistant
- **🎯 Smart Inference**: Automatically carries forward parish/measure from previous questions

## Quick Start

```powershell
# Install dependencies (uv)
uv pip install streamlit pandas folium streamlit-folium requests langchain langchain-community langchain-ollama chromadb

# Run CLI (single-agent)
uv run python main.py

# Multi-agent mode
uv run python main.py --mode multi

# Streamlit GUI (with LangChain features)
uv run streamlit run gui/app.py
```

### Enable LangChain Features in GUI

1. **Start Ollama** (required for RAG features):

   ```powershell
   ollama serve
   ```

2. **Launch the app**:

   ```powershell
   uv run streamlit run gui/app.py
   ```

3. **Enable in sidebar**:

   - ☑️ **Conversational Memory** - Remember context for follow-ups
   - ☑️ **RAG Variable Search** - Semantic search for better variable matching

4. **Try a conversation**:
   ```
   "What are the top 5 tracts in Orleans Parish by median income?"
   → "Now show me poverty rate"  (automatically uses Orleans!)
   ```

### Docker Deployment

```bash
docker compose build
docker compose up
```

Services:

- `ollama`: runs `ollama serve` and stores models in the `ollama-data` volume.
- `app`: builds this repo, runs `scripts/build_doc_index.py`, and launches Streamlit on port 8501.

Visit `http://localhost:8501` after both containers are healthy. The Ollama API is forwarded on `http://localhost:11434` for debugging or model management (`docker compose exec ollama ollama pull phi3:mini`).

## Documentation

- **[Usage Guide](docs/USAGE_GUIDE.md)** - Comprehensive guide with examples and tips
- **[LangChain Features](docs/LANGCHAIN_FEATURES.md)** - NEW: Conversational memory, RAG, and intelligent context
- **[LangChain Quick Start](docs/LANGCHAIN_QUICKSTART.md)** - NEW: Get started with conversational features
- **[Variable Assistant LangChain](docs/VARIABLE_ASSISTANT_LANGCHAIN.md)** - NEW: Memory for variable discovery chat
- **[Multi-Agent Architecture](docs/MULTIAGENT_SUMMARY.md)** - Technical deep dive
- **[Quick Start](docs/QUICKSTART.md)** - Get up and running quickly
- **[Full README](docs/README.md)** - Complete documentation

## Project Structure

```
acs_llm_agent/
├── main.py                 # CLI entry point
├── src/                    # Core application code
│   ├── single_agent/       # Single-agent implementation
│   ├── agents/             # Multi-agent system
│   ├── langchain_features/ # NEW: LangChain enhancements
│   │   ├── conversation_memory.py  # Conversational context tracking
│   │   ├── census_rag.py          # RAG for Census variables
│   │   ├── query_engine.py        # Unified LangChain interface
│   │   └── census_agent.py        # ReAct agent with tools
│   ├── mvp_multiagent.py   # Multi-agent CLI runner
│   ├── acs_tools.py        # Census/TIGER helpers
│   └── geography.py        # Louisiana geography data
├── gui/                    # Streamlit app (with LangChain integration)
├── scripts/                # Utility + ingestion scripts
│   └── windows/            # Windows helpers (bat/ps1)
├── docs/                   # Documentation
│   ├── LANGCHAIN_FEATURES.md           # NEW: LangChain guide
│   ├── LANGCHAIN_QUICKSTART.md         # NEW: Quick start
│   ├── VARIABLE_ASSISTANT_LANGCHAIN.md # NEW: Variable chat memory
│   └── notes/              # Historical notes
├── acs_docs/               # Raw ACS reference PDFs/XLSX
├── cache/                  # DuckDB index + data caches
├── chroma_db/              # NEW: Vector database for RAG
├── tests/                  # Pytest suite
│   └── manual/             # Exploratory/manual tests
└── requirements.txt        # Runtime dependencies
```

## Example Queries

### Standard Queries

```
> What are the top 5 richest census tracts in Orleans Parish?
> Show me areas with poverty over 30% in Caddo Parish
> Find tracts with median income between $40,000 and $75,000
> Which are the most densely populated areas in Lafayette?
```

### 🧠 Conversational Queries (with LangChain Memory)

```
> What are the top 5 tracts in Orleans Parish by median income?
→ [Returns results for Orleans Parish]

> Now show me poverty rate
→ Automatically uses Orleans Parish from previous query!

> What about Lafayette Parish instead?
→ Switches to Lafayette, keeps poverty rate measure

> Also show population density
→ Uses Lafayette Parish, switches to density
```

### 📚 Variable Assistant (with Memory)

```
> What income variables can I ask about?
→ [Shows B19013, B19060, B19080...]

> Tell me more about B19060
→ Remembers you were discussing income variables
→ Provides detailed explanation of B19060

> Which of those works for aggregate household income?
→ Knows "those" refers to income variables from earlier
```

## Architecture Comparison

| Feature                    | Single-Agent | Multi-Agent   |
| -------------------------- | ------------ | ------------- |
| **Speed**                  | 2-5 seconds  | 8-15 seconds  |
| **Accuracy**               | 85-90%       | 90-95%        |
| **Memory**                 | ~2GB         | ~2GB (shared) |
| **Confidence Scores**      | No           | Yes           |
| **Follow-up Support**      | No           | Yes           |
| **LangChain Memory** 🆕    | Optional     | Optional      |
| **RAG Variable Search** 🆕 | Optional     | Optional      |

### LangChain Features Performance

| Feature               | First Use       | Subsequent Use | Storage    |
| --------------------- | --------------- | -------------- | ---------- |
| **Memory Tracking**   | <10ms           | <10ms          | In-memory  |
| **RAG Vector Store**  | 30-60s (builds) | <1s            | ~50-100 MB |
| **Context Inference** | <5ms            | <5ms           | In-memory  |

See [LangChain Features Guide](docs/LANGCHAIN_FEATURES.md) for detailed documentation.

## Requirements

- Python 3.13+
- [Ollama](https://ollama.ai/) with `phi3:mini` model
- Census API key (set `CENSUS_API_KEY` environment variable)

### LangChain Dependencies (Optional)

For conversational features and RAG:

```powershell
uv pip install langchain langchain-community langchain-ollama chromadb
```

**Packages:**

- `langchain==1.0.5` - Core framework
- `langchain-ollama==1.0.0` - Ollama integration
- `langchain-community==0.4.1` - Community tools
- `chromadb==1.3.4` - Vector database for RAG

**Note:** App works without LangChain packages but conversational memory and RAG features will be disabled.

## 🧠 LangChain Features

### Conversational Memory 💬

Ask follow-up questions naturally without repeating context:

```
You: "Show me top 5 tracts in Orleans Parish by income"
→ System remembers: Parish=Orleans, Measure=income

You: "Now show me poverty rate"
→ System infers: Parish=Orleans (from memory), Measure=poverty rate
```

**Features:**

- Tracks last 10 queries with context
- Detects patterns: "now show", "what about", "instead of"
- Separate contexts for main queries and Variable Assistant
- Visual indicators when follow-ups detected

### RAG for Census Variables 📚

Semantic search through 30,000+ Census variables:

```
Query: "household earnings"
→ Traditional: Might miss B19013 (uses keyword "income")
→ RAG: Finds B19013 (understands earnings ≈ income)
```

**Benefits:**

- Better variable matching with synonyms
- Understands related concepts
- Confidence scores for matches
- Works with informal terminology

### How to Use

1. **Enable in Streamlit sidebar:**

   - ☑️ Conversational Memory
   - ☑️ RAG Variable Search

2. **Check conversation history:**

   - Expand "📜 Conversation Context" in sidebar
   - See what the system remembers

3. **Clear when needed:**
   - Click "🗑️ Clear Conversation" to reset

See [LangChain Quick Start](docs/LANGCHAIN_QUICKSTART.md) for detailed guide.

## Contributing

Contributions welcome! Please check the [issues](../../issues) page.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- **U.S. Census Bureau** - ACS data and TIGER/Line shapefiles
- **Ollama** - Local LLM inference
- **LangChain** - Conversational AI framework
- **ChromaDB** - Vector database for semantic search
- **Louisiana parishes** - All 64 parishes supported!
