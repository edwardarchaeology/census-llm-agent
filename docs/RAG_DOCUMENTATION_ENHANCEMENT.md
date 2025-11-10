# RAG Enhancement: ACS Documentation Integration

## Overview

The LangChain RAG system has been enhanced to include **ACS documentation PDFs and Excel files** alongside Census variable metadata. This provides much richer context for semantic search.

## What's Indexed

### Before (Variable Metadata Only)

- **~30,000 Census variables** with:
  - Variable ID (e.g., `B19013_001E`)
  - Label (e.g., "Median Household Income")
  - Concept (e.g., "Income and Benefits")
  - Description
  - Table info

### After (Variables + Documentation)

All of the above **PLUS**:

1. **ACS Definition PDFs** (`acs_docs/*.pdf`):

   - `2023_ACSSubjectDefinitions.pdf` - Subject area definitions
   - `2023GQ_Definitions.pdf` - Group quarters definitions
   - `2023_ACS_Accuracy_Document_Worked_Examples.pdf` - Statistical examples
   - Chunked into ~1200 character segments with 200 char overlap

2. **ACS Data Product List** (`acs_docs/*.xlsx`):
   - Table IDs and descriptions
   - Subject areas
   - Universe definitions
   - Table titles

## Benefits

### 1. Better Semantic Understanding

**Example Query**: "What does universe mean in ACS?"

**Before**: Returns variables with "universe" in metadata (often not helpful)

**After**: Returns actual documentation chunks explaining:

> "Universe refers to the population or housing units for which data are collected..."

### 2. Contextual Variable Discovery

**Example Query**: "How do I calculate poverty rate?"

**Before**: Returns `B17001` (poverty status variable)

**After**: Returns:

- `B17001` poverty variables
- PDF documentation explaining poverty calculation methodology
- Examples from accuracy documents

### 3. Enhanced Variable Assistant

The Variable Assistant chat now has access to official Census Bureau definitions and explanations, not just variable labels.

## How It Works

### Vector Database Structure

```
ChromaDB (./chroma_db)
├── Variables (~30,000 docs)
│   ├── doc_type: "variable"
│   └── metadata: {variable_id, label, concept, ...}
├── PDF Chunks (~1,000+ docs)
│   ├── doc_type: "pdf"
│   └── metadata: {source, chunk, ...}
└── Excel Rows (~500+ docs)
    ├── doc_type: "excel"
    └── metadata: {table_id, subject, title, ...}
```

### Search Methods

#### 1. `search(query, top_k=5, filter_type=None)`

Returns **all document types** ranked by semantic similarity.

```python
results = rag.search("median household income", top_k=5)
# Returns mix of variables + documentation
```

**Filter options**:

- `filter_type="variable"` - Only Census variables
- `filter_type="pdf"` - Only PDF chunks
- `filter_type="excel"` - Only Excel rows
- `filter_type=None` - All types (default)

#### 2. `search_variables_only(query, top_k=5)`

Returns **only Census variables** for backward compatibility.

```python
results = rag.search_variables_only("median household income", top_k=5)
# Returns only variables like B19013_001E
```

#### 3. `get_context_for_query(query, top_k=3)`

Returns formatted context string for LLM prompt augmentation.

## Usage Examples

### Example 1: Variable Discovery with Context

```python
from census_rag import CensusVariableRAG

rag = CensusVariableRAG(include_docs=True)

# Search for income variables + documentation
results = rag.search("median household income trends", top_k=5)

for result in results:
    if result['doc_type'] == 'variable':
        print(f"Variable: {result['variable_id']}")
    elif result['doc_type'] == 'pdf':
        print(f"Documentation: {result['source']}")
        print(f"Content: {result['content'][:200]}...")
```

### Example 2: Understanding ACS Concepts

```python
# Find documentation about specific ACS concepts
results = rag.search("what is a household vs family", top_k=3)

for result in results:
    if result['doc_type'] == 'pdf':
        print(result['content'])  # Official Census definition
```

### Example 3: Integration with Query Engine

The `LangChainQueryEngine` automatically uses enhanced RAG:

```python
from query_engine import LangChainQueryEngine

engine = LangChainQueryEngine()

# Variable suggestions now include documentation context
rag_vars = engine.get_rag_suggestions("poverty rate", top_k=5)

# Get relevant documentation
rag_docs = engine.get_rag_documentation("how to calculate poverty", top_k=3)
```

## Rebuilding the Index

### When to Rebuild

- After adding new PDFs to `acs_docs/`
- After updating existing documentation
- First time setup

### How to Rebuild

```python
from census_rag import CensusVariableRAG

# Rebuild with documentation
rag = CensusVariableRAG(
    rebuild=True,           # Force rebuild
    include_docs=True,      # Include PDFs and Excel
    docs_dir="./acs_docs"   # Documentation directory
)
```

### Command Line Test

```powershell
# Test the enhanced RAG
uv run test_rag_with_docs.py
```

This will:

1. Rebuild the vector database
2. Test searches across all document types
3. Verify backward compatibility

## Performance Considerations

### Initial Build Time

- **Variables only**: ~30-60 seconds
- **Variables + Documentation**: ~2-4 minutes (one-time)

### Storage

- **Variables only**: ~50-100 MB
- **Variables + Documentation**: ~150-250 MB

### Query Speed

- No difference in query speed (same vector search)
- More comprehensive results

## API Changes

### Backward Compatible

Existing code continues to work:

```python
# Still works - returns variables only
matches = engine.get_rag_suggestions(query, top_k=5)
```

### New Methods

```python
# New - get documentation context
docs = engine.get_rag_documentation(query, top_k=3)
```

## Configuration

### Disable Documentation

If you only want variables:

```python
rag = CensusVariableRAG(include_docs=False)
```

### Custom Documentation Directory

```python
rag = CensusVariableRAG(
    include_docs=True,
    docs_dir="/path/to/my/acs/docs"
)
```

## Troubleshooting

### PDFs Not Loading

If PDFs are skipped:

```
⚠️  pdfminer.six not installed - PDF documentation will be skipped
```

**Fix**: Install dependencies

```bash
uv sync
```

### Excel Files Not Loading

Requires `openpyxl`:

```bash
uv pip install openpyxl
```

### Slow Initial Build

Normal! Building embeddings for thousands of documents takes time. Subsequent loads are instant (uses cached `./chroma_db`).

## What's Next

Potential future enhancements:

- Add ACS methodology documents
- Include TIGER/Line geographic documentation
- Add Census subject definitions
- Integrate with main query execution (auto-augment prompts)

## Summary

The enhanced RAG system now provides:

- ✅ Semantic search across 30,000+ variables
- ✅ Official Census Bureau documentation
- ✅ Better context for Variable Assistant
- ✅ Backward compatible API
- ✅ Richer semantic understanding

This makes the system significantly more helpful for users trying to understand ACS data!
