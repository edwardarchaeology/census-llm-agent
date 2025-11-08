# Quick Start Guide

## Choosing the Right Mode

### Use Single-Agent Mode When:

- ✅ You need **fast responses** (2-5 seconds)
- ✅ Queries are **simple and clear**
- ✅ You're **prototyping or testing**
- ✅ You don't need confidence feedback

**Example**:

```bash
python main.py
# or
python main.py --mode single
```

### Use Multi-Agent Mode When:

- ✅ **Accuracy is critical**
- ✅ Queries are **complex or ambiguous**
- ✅ You need **confidence scores**
- ✅ You want **follow-up question support**
- ✅ It's a **production deployment**

**Example**:

```bash
python main.py --mode multi
```

## Common Usage Patterns

### 1. Quick Data Lookup (Single-Agent)

```bash
python main.py
> What are the top 5 richest tracts in Orleans Parish?
```

### 2. Exploratory Analysis (Multi-Agent)

```bash
python main.py --mode multi
> Show me high-poverty areas in Louisiana
> Now just in Caddo Parish
> What about population density there?
```

### 3. Setting Default Mode via Environment

```powershell
# PowerShell
$env:AGENT_MODE = "multi"
python main.py  # Will use multi-agent mode

# Or in one line
$env:AGENT_MODE="multi"; python main.py
```

## Query Examples by Type

### Top/Bottom Queries

```
Single-agent: "top 5 income tracts in New Orleans"
Multi-agent:  "What are the top 5 census tracts in Caddo Parish by poverty rate?"
```

### Filter Queries

```
Single-agent: "tracts with poverty over 30%"
Multi-agent:  "Find all tracts in Lafayette Parish with poverty rate under 10%"
```

### Range Queries

```
Single-agent: "income between 50k and 80k"
Multi-agent:  "Show me tracts with median income between $40,000 and $75,000 in St. Tammany"
```

### Geographic Queries

```
Single-agent: "highest income in New Orleans"
Multi-agent:  "What are the wealthiest census tracts in East Baton Rouge Parish?"
```

## Performance Comparison

| Metric                 | Single-Agent | Multi-Agent |
| ---------------------- | ------------ | ----------- |
| Query Time             | 2-5 sec      | 8-15 sec    |
| Simple Query Accuracy  | 85-90%       | 90-95%      |
| Complex Query Accuracy | 60-70%       | 85-95%      |
| Geography Resolution   | Good         | Excellent   |
| Variable Matching      | Good         | Excellent   |
| Error Recovery         | Basic        | Advanced    |
| Confidence Feedback    | None         | Yes         |
| Follow-up Support      | No           | Yes         |

## When Multi-Agent Shines

### Ambiguous Measures

```
Query: "Show me diverse neighborhoods"

Single-agent: Guesses what "diverse" means → may be wrong
Multi-agent:  Returns confidence: 0.45 (LOW)
             Asks: "Did you mean racial diversity, age diversity, or income diversity?"
```

### Complex Geography

```
Query: "St. Tammany Parish poverty"

Single-agent: May miss "St." variations
Multi-agent:  Resolves "St. Tammany", "Saint Tammany", "St Tammany Parish" all correctly
             Returns confidence: 0.98
```

### Variable Selection

```
Query: "median income"

Single-agent: Basic fuzzy match → may pick wrong variable
Multi-agent:  Evaluates top 5 candidates
             Returns: "Median household income" vs "Median family income"
             Confidence: 0.95
             Reasoning: "Household income more common than family income"
```

## Troubleshooting

### Query Takes Too Long (Multi-Agent)

- Consider switching to single-agent for simple queries
- Check Ollama is running (`ollama ps`)
- Verify phi3:mini is loaded

### Low Confidence Warning (Multi-Agent)

```
>>> Variable: B19013_001E
    Label: Median household income
    Confidence: 0.45
>>> WARNING: Low confidence (0.45)
```

**What it means**: The system is unsure about your request
**What to do**: Rephrase query to be more specific

### Wrong Geography Detected

```
>>> Geography: Orleans Parish (FIPS: 071) (confidence: 0.60)
```

**If wrong**: Be more explicit

- Instead of: "income in the city"
- Use: "income in Lafayette Parish"

## Tips for Best Results

### 1. Be Specific About Geography

✅ Good: "poverty in Caddo Parish"
❌ Vague: "poverty in the north"

### 2. Use Standard Measure Names

✅ Good: "median income", "poverty rate", "population density"
❌ Unclear: "how much people make", "poorness"

### 3. Include Units When Filtering

✅ Good: "income over $75,000" or "poverty over 20%"
❌ Unclear: "income over 75" (dollars? thousands?)

### 4. Start Simple (Single-Agent), Upgrade If Needed

1. Try query in single-agent mode
2. If result seems wrong, switch to multi-agent
3. Check confidence scores
4. Refine query based on feedback

## Advanced: Programmatic Usage

### Single-Agent

```python
from mvp import run_query, print_result

result = run_query("top 5 poverty in Caddo Parish")
print_result(result)
```

### Multi-Agent

```python
from mvp_multiagent import run_multiagent_query, print_result

result = run_multiagent_query("top 5 poverty in Caddo Parish", verbose=True)
print_result(result)

# Check confidence
if result.attrs.get("confidence", 1.0) < 0.7:
    print("Warning: Low confidence result")
```

## See Also

- `README.md` - Full documentation
- `MULTIAGENT_SUMMARY.md` - Multi-agent architecture details
- `python main.py --compare` - Detailed comparison
- `python main.py --help` - Command-line options
