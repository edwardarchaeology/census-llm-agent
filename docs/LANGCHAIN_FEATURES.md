# LangChain Features Documentation

## Overview

The Louisiana Census Data Explorer has been enhanced with LangChain features to provide:

- **Conversational Memory**: Remember context across multiple queries
- **RAG (Retrieval Augmented Generation)**: Semantic search for better Census variable matching
- **Query Engine**: Unified interface combining memory and RAG

## Features

### 1. Conversational Memory 💬

Enables follow-up questions without repeating context.

**Example conversation:**

```
User: "What are the top 5 tracts in Orleans Parish by median income?"
→ Returns top 5 tracts in Orleans Parish

User: "Now show me poverty rate"
→ Automatically infers Orleans Parish from previous context
→ Returns poverty rate for Orleans Parish
```

**How it works:**

- Tracks last 10 queries with their context (parish, measure, variable)
- Detects follow-up patterns: "now", "also", "what about", "instead of", "same for"
- Infers missing geography or measure from conversation history
- Provides formatted history for LLM context augmentation

**API:**

```python
from conversation_memory import ConversationalMemory

memory = ConversationalMemory(max_history=10)

# Add a query
memory.add_query(
    query="What are the top 5 tracts in Orleans by income?",
    parish="Orleans Parish",
    county_fips="071",
    measure="median household income",
    variable_id="B19013_001E",
    result_count=5,
    successful=True
)

# Check if follow-up
is_followup = memory.is_follow_up("Now show me poverty rate")  # True

# Infer missing context
context = memory.infer_missing_context("Now show me poverty rate")
# Returns: {"parish": "Orleans Parish", "county_fips": "071"}

# Get conversation summary for LLM
summary = memory.get_context_summary()
```

**Follow-up patterns detected:**

- "now show me..."
- "also show..."
- "what about..."
- "instead of..."
- "same for..."
- "how about..."

### 2. RAG for Census Variables 📚

Uses semantic search to find better Census variable matches.

**Benefits:**

- Understands synonyms and related concepts
- Better handles ambiguous queries
- Provides confidence scores for matches
- Can find variables even when exact keywords don't match

**How it works:**

- Builds ChromaDB vector store with all 30,000+ Census variables
- Uses OllamaEmbeddings (phi3:mini) for semantic understanding
- Returns top-k most relevant variables with similarity scores
- Can augment LLM prompts with contextual variable suggestions

**API:**

```python
from census_rag import CensusVariableRAG

rag = CensusVariableRAG()  # Lazy-loads on first use

# Search for variables
results = rag.search("median household income", top_k=5)

# Results format:
[
    {
        "variable_id": "B19013_001E",
        "label": "Median household income in the past 12 months...",
        "score": 0.95
    },
    ...
]

# Get formatted context for LLM
context = rag.get_context_for_query("What is the median income?")
# Returns formatted string with top variable suggestions
```

**Performance:**

- First initialization: ~30-60 seconds (builds vector embeddings)
- Subsequent queries: <1 second (uses cached vectors)
- Vector store saved to `./chroma_db` directory

### 3. Query Engine 🔧

Unified interface combining memory and RAG with the Census query system.

**Features:**

- Seamlessly integrates conversational memory
- Optionally uses RAG for variable selection
- Falls back gracefully if LangChain features unavailable
- Tracks execution metadata (follow-ups, inferred context, RAG suggestions)

**API:**

```python
from query_engine import LangChainQueryEngine

engine = LangChainQueryEngine()

# Process a query
result = engine.process_query(
    query="What are the top 5 tracts in Orleans by income?",
    mode="single",  # or "multi"
    verbose=True,
    use_memory=True,
    use_rag=True
)

# Result format:
{
    "success": True,
    "dataframe": pd.DataFrame(...),
    "label": "Median household income...",
    "is_follow_up": False,
    "inferred_context": {},
    "rag_context": [...],
    "conversation_summary": "...",
    "debug_info": {...}
}

# Get conversation history
history = engine.get_conversation_history()

# Clear memory
engine.clear_memory()

# Get RAG suggestions
suggestions = engine.get_rag_suggestions("poverty rate", top_k=5)
```

## Streamlit GUI Integration

### Enabling Features

In the Streamlit sidebar:

**🧠 LangChain Features** section:

- ☑️ **Conversational Memory**: Enable follow-up question support
- ☑️ **RAG Variable Search**: Use semantic search for variables

### Visual Indicators

When enabled, you'll see:

- **Active features badge**: `🧠 LangChain Features Active: 💬 Memory + 📚 RAG`
- **Follow-up detection**: `🔄 Follow-up question detected!` with inferred context
- **RAG suggestions**: Expandable section showing top variable matches
- **Conversation history**: Collapsible view of recent queries

### Example Workflow

1. **Enable features** in sidebar:

   - ✅ Conversational Memory
   - ✅ RAG Variable Search

2. **First query:**

   ```
   "What are the top 5 census tracts in Orleans Parish by median income?"
   ```

   - System processes normally
   - Stores context: Parish = Orleans, Measure = median income

3. **Follow-up query:**

   ```
   "Now show me poverty rate"
   ```

   - 🔄 Detects follow-up pattern
   - Infers: Parish = Orleans (from history)
   - Shows: "Using context from previous query: Parish: Orleans Parish"

4. **Switch geography:**
   ```
   "What about Lafayette Parish instead?"
   ```
   - Detects: "instead" pattern
   - Updates: Parish = Lafayette, keeps Measure = poverty rate

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit GUI (app.py)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Sidebar: Memory ☑  RAG ☑                           │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            LangChain Query Engine (query_engine.py)         │
│  ┌─────────────────┐              ┌────────────────────┐    │
│  │  Memory Check   │──────────────│  RAG Search        │    │
│  │  - Follow-up?   │              │  - Semantic match  │    │
│  │  - Infer context│              │  - Top-k results   │    │
│  └─────────────────┘              └────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Single/Multi-Agent Query System                    │
│  - Geography resolution (parish → FIPS)                     │
│  - Variable selection (fuzzy + LLM)                         │
│  - Census API query                                         │
│  - Result formatting                                        │
└─────────────────────────────────────────────────────────────┘
```

## Dependencies

Required packages:

```bash
uv pip install --no-cache langchain langchain-community langchain-ollama chromadb
```

**Package versions:**

- `langchain==1.0.5`
- `langchain-ollama==1.0.0`
- `langchain-community==0.4.1`
- `chromadb==1.3.4`

**External dependencies:**

- Ollama server running on `localhost:11434`
- `phi3:mini` model loaded (`ollama pull phi3:mini`)

## Performance Considerations

### RAG Initialization

- **First run**: 30-60 seconds to build vector embeddings for 30K+ variables
- **Subsequent runs**: <1 second (loads from `./chroma_db` cache)
- **Disk usage**: ~50-100 MB for vector store

### Memory Usage

- Minimal overhead: ~1 KB per query in history
- Max 10 queries stored (configurable)
- Cleared on app restart or manual clear

### Query Speed Impact

- **Memory check**: <10ms
- **RAG search**: <1s (after initialization)
- **Total overhead**: <1s per query

### Recommendations

- Enable RAG if variable selection is problematic
- Enable Memory for exploratory conversations
- Disable both for fastest single queries

## Troubleshooting

### RAG not loading

**Symptom:** "RAG system unavailable" warning

**Solutions:**

1. Check Ollama is running: `ollama ps`
2. Verify phi3:mini is loaded: `ollama pull phi3:mini`
3. Check disk space for vector store (~100 MB)
4. Delete `./chroma_db` and rebuild: `rm -rf ./chroma_db`

### Memory not working

**Symptom:** Follow-ups don't infer context

**Solutions:**

1. Ensure "Conversational Memory" is checked in sidebar
2. Verify previous query was successful (stores in memory)
3. Check conversation history in sidebar expander
4. Try clearing memory: "🗑️ Clear Conversation" button

### Import errors

**Symptom:** `ModuleNotFoundError: No module named 'langchain'`

**Solutions:**

```bash
# Reinstall packages
uv pip install --no-cache langchain langchain-community langchain-ollama chromadb

# Verify installation
uv pip list | Select-String "langchain|chromadb"
```

## Testing

Run integration tests:

```bash
python test_langchain_integration.py
```

Expected output:

```
Testing LangChain Integration
============================================================

1. Testing imports...
   ✅ ConversationalMemory imported
   ✅ CensusVariableRAG imported
   ✅ LangChainQueryEngine imported

2. Testing conversational memory...
   ✅ Memory initialized
   ✅ Follow-up detection works
   ✅ Query added to memory
   ✅ Context inference works: {'parish': 'Orleans Parish', ...}

3. Testing RAG system...
   ⏳ Initializing RAG (this may take a minute first time)...
   ✅ RAG initialized
   ✅ Search returned 3 results
   Top match: B19013_001E - Median household income...
   ✅ RAG search works correctly

4. Testing query engine...
   ✅ Query engine initialized
   Testing conversation flow:
   Query 1: 'What are the top 5 tracts in Orleans Parish by median income?'
   ✅ First query successful: 5 results
   Is follow-up: False
   Query 2: 'Now show me poverty rate'
   ✅ Follow-up query successful: 184 results
   Is follow-up: True
   Inferred context: {'parish': 'Orleans Parish', 'county_fips': '071'}
   ✅ Memory correctly inferred parish from history!

============================================================
✅ All tests passed! LangChain integration is working.
```

## Future Enhancements

Potential additions:

1. **LangGraph**: Multi-step reasoning for complex queries
2. **Structured Output Parsers**: Pydantic validation for responses
3. **Semantic Caching**: Cache similar queries (not just exact matches)
4. **Prompt Templates**: Few-shot examples for better LLM responses
5. **Agent Tools**: Autonomous agent that decides which tools to use
6. **Chain-of-Thought**: Show reasoning steps for variable selection

## References

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Census API Documentation](https://www.census.gov/data/developers/guidance/api-user-guide.html)
