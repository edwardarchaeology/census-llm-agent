# Louisiana Census Data Agent 🗺️

A dual-architecture LLM-powered agent for querying Louisiana census tract data using natural language.

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green.svg)](https://ollama.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🎯 **Dual Architecture**: Choose between fast single-agent or accurate multi-agent mode
- 🗣️ **Natural Language**: Ask questions in plain English
- 📊 **Louisiana Coverage**: All 64 parishes + major cities
- 🔍 **Smart Resolution**: Fuzzy matching for measures and geography
- 💾 **Intelligent Caching**: Multi-layer caching for fast responses
- 📈 **Rich Metrics**: Population, income, poverty, race, age, and more
- 🎨 **Clean Output**: ASCII-safe formatting for terminal display

## 🚀 Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Run with single-agent (fast)
python main.py

# Run with multi-agent (accurate)
python main.py --mode multi

# Compare architectures
python main.py --compare
```

## 📖 Documentation

- **[Usage Guide](docs/USAGE_GUIDE.md)** - Comprehensive guide with examples and tips
- **[Multi-Agent Architecture](docs/MULTIAGENT_SUMMARY.md)** - Technical deep dive
- **[Quick Start](docs/QUICKSTART.md)** - Get up and running quickly
- **[Full README](docs/README.md)** - Complete documentation

## 📁 Project Structure

```
acs_llm_agent/
├── main.py                    # Unified entry point
├── src/                       # Source code
│   ├── single_agent/          # Single-agent implementation
│   │   ├── mvp.py            # Main CLI
│   │   ├── intent.py         # Intent extraction
│   │   └── resolver.py       # Variable resolution
│   ├── agents/                # Multi-agent system
│   │   ├── base_agent.py     # Base agent class
│   │   ├── orchestrator_agent.py
│   │   ├── geography_agent.py
│   │   ├── variable_agent.py
│   │   └── query_planner_agent.py
│   ├── mvp_multiagent.py     # Multi-agent CLI
│   ├── acs_tools.py          # Census API integration
│   └── geography.py          # Louisiana geography data
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
├── docs/                      # Documentation
└── cache/                     # Data cache

```

## 🎯 Example Queries

```
> What are the top 5 richest census tracts in Orleans Parish?
> Show me areas with poverty over 30% in Caddo Parish
> Find tracts with median income between $40,000 and $75,000
> Which are the most densely populated areas in Lafayette?
```

## 🏗️ Architecture Comparison

| Feature               | Single-Agent | Multi-Agent   |
| --------------------- | ------------ | ------------- |
| **Speed**             | 2-5 seconds  | 8-15 seconds  |
| **Accuracy**          | 85-90%       | 90-95%        |
| **Memory**            | ~2GB         | ~2GB (shared) |
| **Confidence Scores** | ❌           | ✅            |
| **Follow-up Support** | ❌           | ✅            |

See [Usage Guide](docs/USAGE_GUIDE.md) for detailed comparison.

## 📦 Requirements

- Python 3.13+
- [Ollama](https://ollama.ai/) with `phi3:mini` model
- Census API key (set `CENSUS_API_KEY` environment variable)

## 🤝 Contributing

Contributions welcome! Please check the [issues](../../issues) page.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **U.S. Census Bureau** - ACS data and TIGER/Line shapefiles
- **Ollama** - Local LLM inference
- **Louisiana parishes** - All 64 parishes supported!
