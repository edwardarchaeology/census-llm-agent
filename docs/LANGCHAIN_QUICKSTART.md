# LangChain Features - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start Ollama (Optional - for RAG features)

```powershell
# In a PowerShell terminal
ollama serve
```

> **Note:** Conversational Memory works without Ollama! Only RAG semantic search requires it.

### Step 2: Launch the App

```powershell
# In the project directory
streamlit run gui/app.py
```

### Step 3: Enable Features

In the Streamlit sidebar, under **🧠 LangChain Features**:

- ☑️ Check **💬 Conversational Memory**
- ☑️ Check **📚 RAG Variable Search** (if Ollama running)

---

## 💬 Try a Conversation

### Example 1: Simple Follow-Up

```
You: "What are the top 5 census tracts in Orleans Parish by median income?"

Bot: [Shows top 5 tracts]

You: "Now show me poverty rate"

Bot: 🔄 Follow-up question detected!
     Using context from previous query: Parish: Orleans Parish
     [Shows poverty rate for Orleans Parish]
```

### Example 2: Changing Geography

```
You: "Show me the highest income tracts in Orleans Parish"

Bot: [Shows Orleans results]

You: "What about Lafayette Parish instead?"

Bot: 🔄 Follow-up question detected!
     [Shows Lafayette results for same measure]
```

### Example 3: Exploring Different Measures

```
You: "Find tracts with low poverty in St. Tammany Parish"

Bot: [Shows poverty results for St. Tammany]

You: "Also show population density"

Bot: 🔄 Follow-up question detected!
     [Shows population density for St. Tammany]
```

---

## 🎯 Features at a Glance

### Conversational Memory 💬

**What it does:** Remembers context from previous queries

**When to use:**

- Exploring different measures in the same parish
- Comparing multiple parishes for the same measure
- Asking follow-up questions without repeating yourself

**Patterns it understands:**

- "Now show me..."
- "Also show..."
- "What about..."
- "Instead of..."
- "Same for..."

### RAG Variable Search 📚

**What it does:** Uses semantic search to find better Census variables

**When to use:**

- Query uses synonyms or informal terms
- Not sure of exact Census terminology
- Want better variable suggestions

**Examples:**

- "household earnings" → Finds B19013 (Median Household Income)
- "poor people" → Finds S1701 (Poverty Status)
- "people living in apartments" → Finds B25024 (Units in Structure)

---

## 📊 Visual Indicators

### When Memory is Active

```
🧠 LangChain Features Active: 💬 Memory
```

### When Follow-Up Detected

```
🔄 Follow-up question detected!
Using context from previous query: Parish: Orleans Parish
```

### When RAG Finds Matches

```
📚 RAG Variable Suggestions ▼
   B19013_001E (score: 0.95)
   Median household income in the past 12 months...
```

### Conversation History

Click **📜 Conversation Context** in sidebar to see:

```
Previous queries:
1. Query: "What are the top 5 tracts in Orleans by income?"
   Parish: Orleans Parish
   Measure: median household income
   Results: 5 tracts

Current context:
Parish: Orleans Parish
Measure: median household income
```

---

## 🔧 Troubleshooting

### "RAG system unavailable"

**Cause:** Ollama is not running

**Solution:**

```powershell
# Start Ollama
ollama serve

# Verify it's running
ollama ps
```

### "Follow-up not detected"

**Cause:** Conversational Memory is disabled

**Solution:**

- Check ☑️ **Conversational Memory** in sidebar
- Make sure previous query was successful (stores context)

### Clear conversation history

**When:** Want to start fresh, or memory has wrong context

**How:** Click **🗑️ Clear Conversation** button in sidebar

---

## ⚙️ Configuration

### Memory Settings

- **Max history:** 10 queries (default)
- **Persistence:** In-memory only (clears on restart)
- **Storage:** ~1 KB per query

### RAG Settings

- **Vector store:** `./chroma_db` directory
- **First build:** 30-60 seconds
- **Subsequent loads:** <1 second
- **Storage:** ~50-100 MB

---

## 🎓 Tips & Best Practices

### 1. Use Natural Language

✅ Good: "Now show me poverty rate"  
❌ Avoid: "Query: S1701_C03_001E for FIPS 071"

### 2. Build on Previous Queries

✅ Good conversation flow:

```
"Top 5 tracts in Orleans by income"
→ "Now show poverty rate"
→ "What about Lafayette instead?"
```

❌ Repetitive:

```
"Top 5 tracts in Orleans by income"
→ "Top 5 tracts in Orleans by poverty rate"
→ "Top 5 tracts in Lafayette by poverty rate"
```

### 3. Clear Memory When Switching Topics

If you switch to a completely different analysis:

- Click **🗑️ Clear Conversation**
- Start fresh without old context

### 4. Enable Memory for Exploratory Analysis

Best for:

- Comparing multiple measures in one parish
- Exploring different parishes for one measure
- Interactive data exploration sessions

Disable for:

- One-off queries
- Automated/scripted queries
- When you want independent queries

---

## 📚 Learn More

- **Full Documentation:** `docs/LANGCHAIN_FEATURES.md`
- **Implementation Details:** `docs/LANGCHAIN_IMPLEMENTATION_SUMMARY.md`
- **Test Examples:** `test_langchain_integration.py`

---

## 🆘 Need Help?

### Check the Conversation History

Expand **📜 Conversation Context** in sidebar to see what the system remembers

### View Debug Output

Enable **"Show detailed output"** in Settings to see:

- LLM reasoning
- Variable selection process
- Geography resolution
- RAG search results

### Common Issues

**Q: Follow-ups don't work**  
A: Make sure Conversational Memory is ☑️ checked

**Q: Wrong variables selected**  
A: Enable RAG Variable Search for better semantic matching

**Q: RAG is slow**  
A: First run builds vector store (30-60s). Subsequent runs are fast (<1s)

**Q: Memory has wrong context**  
A: Click "🗑️ Clear Conversation" to start fresh

---

**Ready to explore Louisiana Census data with conversational AI! 🎉**
