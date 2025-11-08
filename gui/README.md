# 🗺️ Louisiana Census Data Explorer - GUI

Beautiful, interactive web interface for querying Louisiana census tract data with natural language.

![Streamlit GUI](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=flat-square&logo=streamlit)
![Status](https://img.shields.io/badge/Status-Ready-success?style=flat-square)

## ✨ Features

- 🔍 **Natural Language Queries** - Ask questions in plain English
- 🗺️ **Interactive Maps** - View results on Louisiana map with Folium
- 📊 **Data Tables** - Sortable, filterable results
- 📥 **CSV/JSON Export** - Download results and raw data
- ⚡ **Mode Switching** - Choose between fast single-agent or accurate multi-agent
- 💾 **Smart Caching** - Instant results for repeated queries
- 📜 **Query History** - Quick access to recent queries
- 🎨 **Beautiful UI** - Professional design out of the box

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Using UV (recommended)
scripts\\windows\\setup_uv.bat
# Choose option 1 for clean install

# OR using pip
pip install -r requirements.txt
```

### 2. Start Ollama

```powershell
# In a separate terminal
ollama serve

# Make sure phi3:mini is available
ollama pull phi3:mini
```

### 3. Launch GUI

```powershell
# Easy way
scripts\\windows\\run_gui.bat

# OR manually
streamlit run gui\app.py
```

### 4. Open Browser

Navigate to: **http://localhost:8501**

## 🎯 Usage

### Example Queries

Try these natural language queries:

```
What are the top 5 census tracts in Orleans Parish by poverty rate?

Show me tracts with median income over $75,000 in St. Tammany Parish

Find areas with population density above 5000 in Lafayette

Which tracts in Caddo Parish have poverty rate under 15%?

Top 10 wealthiest tracts in East Baton Rouge Parish
```

### Interface Overview

```
┌─────────────────────────────────────────────────────┐
│  🗺️ Louisiana Census Data Explorer                  │
├─────────────────────────────────────────────────────┤
│  Sidebar:                    Main Panel:            │
│  ├─ ⚙️ Settings              ├─ 🔍 Query Input      │
│  │  ├─ Agent Mode            ├─ 💡 Examples         │
│  │  └─ Verbose Output        ├─ 🗺️ Map Tab          │
│  ├─ ℹ️ About                 ├─ 📋 Table Tab        │
│  ├─ 📜 Recent Queries        └─ 📥 Downloads Tab   │
│  └─ 🗑️ Clear Cache                                  │
└─────────────────────────────────────────────────────┘
```

## 🎛️ Settings

### Agent Mode

**⚡ Single-Agent (Fast)**

- Speed: 2-5 seconds
- Best for: Simple, clear queries
- Perfect for: Quick exploration

**🤖 Multi-Agent (Accurate)**

- Speed: 8-15 seconds
- Best for: Complex queries, ambiguous requests
- Features: Confidence scores, better accuracy
- Perfect for: Production analysis

### Verbose Output

Enable to see:

- Agent reasoning process
- Variable resolution steps
- Geography matching details
- Confidence calculations

## 📥 Download Options

### 1. Results CSV

- Filtered results as displayed
- GEOID, tract name, value
- Ready for analysis

### 2. Raw Data CSV

- All original columns
- Complete census data
- For advanced analysis

### 3. JSON Export

- Structured data format
- Machine-readable
- API integration

## 🔧 Configuration

### Environment Variables

```powershell
# Set Ollama endpoint (if not default)
$env:OLLAMA_ENDPOINT = "http://localhost:11434"

# Set Census API key
$env:CENSUS_API_KEY = "your_key_here"

# Set default agent mode
$env:AGENT_MODE = "multi"
```

### Streamlit Config

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
address = "0.0.0.0"

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## 🎨 Features in Detail

### Smart Caching

- **Query Results**: Cached per mode + query
- **Variable Catalog**: Cached for 1 hour
- **Agent Initialization**: One-time per session
- **Instant Re-runs**: Typing doesn't trigger queries

### Interactive Map

- **Base Map**: OpenStreetMap tiles
- **Tract Markers**: Click for details
- **Popups**: Show tract name, value, GEOID
- **Auto-centering**: Focuses on Louisiana

### Data Table

- **Sortable**: Click column headers
- **Searchable**: Built-in filtering
- **Summary Stats**: Mean, median, std dev
- **Row Count**: Total tracts displayed

## 🐛 Troubleshooting

### "Connection Error"

```
❌ Error: Connection refused

Solution:
1. Check Ollama is running: ollama ps
2. Verify endpoint: curl http://localhost:11434/api/tags
3. Start if needed: ollama serve
```

### "No module named streamlit"

```
Solution:
1. Install dependencies: scripts\\windows\\setup_uv.bat
2. OR: pip install -r requirements.txt
3. Verify: streamlit --version
```

### "Page not loading"

```
Solution:
1. Check port 8501 is not in use
2. Try: streamlit run gui\app.py --server.port 8502
3. Check firewall settings
```

### Slow Performance

```
Tips:
1. Use cache (automatic)
2. Try single-agent mode for speed
3. Check Ollama model is loaded: ollama ps
4. Clear cache if needed (sidebar button)
```

## 📊 Performance

| Operation        | Time  | Notes                    |
| ---------------- | ----- | ------------------------ |
| **First Load**   | 2-3s  | Loading variable catalog |
| **Agent Init**   | 1-2s  | Creating agent instances |
| **Single Query** | 2-5s  | Single-agent mode        |
| **Multi Query**  | 8-15s | Multi-agent mode         |
| **Cached Query** | <0.1s | Instant from cache       |
| **Map Render**   | <1s   | Folium rendering         |

## 🌐 Deployment

### Local (Current)

```powershell
streamlit run gui\app.py
# Access: http://localhost:8501
```

### Network Access

```powershell
streamlit run gui\app.py --server.address 0.0.0.0
# Access: http://your-ip:8501
```

### Streamlit Cloud (Free)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo
4. Deploy!

## 📝 Code Structure

```
gui/
├── app.py                  # Main Streamlit application
├── README.md              # This file
└── components/            # Future: Reusable UI components
```

### Key Functions

```python
# Caching & Init
@st.cache_resource
def init_app()              # One-time initialization

# Query Execution
def execute_query()         # Run queries with caching

# UI Components
def render_sidebar()        # Settings & info
def render_map()           # Interactive Folium map
def render_data_table()    # Results table
def render_download_buttons()  # CSV/JSON exports
```

## 🔮 Roadmap

- [ ] Save/load query sessions
- [ ] Export map as image
- [ ] Compare multiple queries
- [ ] Visualization charts (bar, line, choropleth)
- [ ] Advanced filters (multi-variable)
- [ ] Batch query processing
- [ ] User annotations on map
- [ ] Share query via URL

## 🤝 Contributing

To add features:

1. Create new component in `gui/components/`
2. Import in `app.py`
3. Add to appropriate tab or section
4. Test with `streamlit run gui\app.py`

## 📄 License

MIT License - Same as parent project

---

**Built with ❤️ using Streamlit**
