# Variable Assistant LangChain Integration

## Overview

The Variable Assistant chat interface now has its own **separate** LangChain conversational memory system, independent from the main query interface.

## Why Separate Contexts?

### Main Query Interface Context

- **Purpose:** Execute Census data queries
- **Remembers:** Parish selections, measures (income, poverty), variable choices
- **Use Case:** "Show top tracts in Orleans by income" → "Now show poverty rate"

### Variable Assistant Context

- **Purpose:** Learn about Census variables
- **Remembers:** Which variables were discussed, variable IDs, topics explored
- **Use Case:** "What income variables exist?" → "Tell me more about B19060"

**They don't interfere with each other!**

Example workflow:

```
Main Query: "Show top 5 tracts in Orleans by median income"
[Remembers: Parish=Orleans, Measure=median income]

Variable Chat: "What other income variables can I ask about?"
[Does NOT affect main query context]

Variable Chat: "Tell me more about B19060"
[Remembers: Discussing B19060, income variables]

Main Query: "Now show poverty rate"
[Still uses Orleans from earlier main query]
```

---

## Features

### 1. **Conversational Memory** 💬

Tracks up to 15 recent variable discussions with:

- Query text
- Variables discussed (variable IDs)
- Number of suggestions returned
- Success/failure status

### 2. **Context Viewer** 📜

Collapsible "Variable Chat Context" expander shows:

- Last 5 variable discussions
- Variables mentioned in each discussion
- Number of suggestions found
- Currently active variables

### 3. **Clear Memory** 🗑️

"Clear chat" button now:

- Clears chat history
- Resets agent memory
- Clears LangChain conversation memory

---

## Implementation Details

### Session State

```python
st.session_state.variable_chat_memory = ConversationalMemory(max_history=15)
```

### Memory Tracking

When a user asks about variables, the system tracks:

```python
memory.add_query(
    query="What income variables exist?",
    measure=None,  # Variable chat doesn't track measures
    variable_id="B19013_001E, B19060_001E, B19080_001E",  # Top 3 discussed
    result_count=12,  # Number of variable suggestions
    successful=True
)
```

### Context Display Format

```markdown
**Recent Variable Discussions:**

1. _What other income variables can I ask about?_

   - Variables: B19013_001E, B19060_001E, B19080_001E
   - Found: 12 suggestion(s)

2. _Tell me more about B19060_
   - Variables: B19060_001E
   - Found: 5 suggestion(s)

**Currently Discussing:**
Variables: B19060_001E
```

---

## Code Architecture

### Modified Files

**`gui/app.py`:**

1. **`init_session_state()`** - Added Variable Assistant memory initialization

   ```python
   if "variable_chat_memory" not in st.session_state and LANGCHAIN_AVAILABLE:
       st.session_state.variable_chat_memory = ConversationalMemory(max_history=15)
   ```

2. **`reset_variable_chat_history()`** - Clears LangChain memory

   ```python
   if st.session_state.get("variable_chat_memory"):
       st.session_state.variable_chat_memory.clear()
   ```

3. **`_handle_variable_chat_prompt()`** - Tracks discussions in memory

   ```python
   discussed_variables = [c.get("variable_id") for c in candidates]
   variable_ids = ", ".join(discussed_variables[:3])
   memory.add_query(query=question, variable_id=variable_ids, ...)
   ```

4. **`_format_variable_chat_context()`** - NEW: Formats context for display

   - Shows last 5 discussions
   - Displays variables mentioned
   - Shows suggestion counts

5. **`render_variable_chatbox()`** - Displays context expander
   ```python
   with st.expander("📜 Variable Chat Context", expanded=False):
       st.markdown(context_summary)
   ```

---

## Usage

### For Users

1. **Open Variable Assistant** (in main app tabs)
2. **Ask about variables:**

   ```
   "What income variables can I ask about?"
   → System shows B19013, B19060, etc.
   ```

3. **Follow up naturally:**

   ```
   "Tell me more about B19060"
   → System remembers you were discussing income variables
   ```

4. **Check context:**

   - Click "📜 Variable Chat Context" to see what you've discussed
   - See which variables are currently in context

5. **Clear when needed:**
   - Click "Clear chat" to reset everything
   - Useful when switching to a completely different topic

### For Developers

**Add custom tracking:**

```python
# Track additional metadata
memory.add_query(
    query=user_question,
    variable_id=", ".join(variable_ids[:3]),
    result_count=len(candidates),
    successful=True,
    # Add custom fields to QueryContext if needed
)
```

**Customize context display:**

```python
def _format_variable_chat_context(memory):
    # Modify this function to change what's shown
    # in the context viewer
    pass
```

---

## Benefits

### 1. **Better Variable Discovery**

Users can have natural conversations about variables without repeating context:

```
"What poverty variables exist?"
→ [System shows S1701, B17001, etc.]

"Which of those works for children?"
→ [System knows "those" = poverty variables from previous question]
```

### 2. **Separate Contexts**

Main queries and variable learning don't interfere:

- Can explore variables while maintaining main query context
- Can switch between data querying and learning freely

### 3. **Transparency**

Context viewer shows exactly what the system remembers:

- No "black box" behavior
- Users can verify what's in memory
- Clear button provides easy reset

### 4. **Consistency**

Same LangChain memory system used for both:

- Main query interface
- Variable Assistant chat
- Familiar patterns, less code duplication

---

## Future Enhancements

Potential improvements:

1. **Variable Relationship Tracking**

   - Remember that B19013 and B19060 are both income-related
   - Suggest related variables automatically

2. **Topic Clustering**

   - Group discussions by topic (income, poverty, housing)
   - Show "You've been exploring income variables" summary

3. **Smart Suggestions**

   - "You asked about B19013 earlier, also consider B19013_001E"
   - Context-aware variable recommendations

4. **Export Context**

   - Download conversation history
   - Save frequently discussed variables

5. **Cross-Reference with Main Queries**
   - If user queries for income in main interface, highlight B19013 in variable chat
   - Show "You used this variable in recent queries"

---

## Testing

### Manual Test Cases

1. **Basic Memory:**

   ```
   Ask: "What income variables exist?"
   → Check context shows this query

   Ask: "Tell me more about the first one"
   → Verify system remembers previous variables
   ```

2. **Context Viewer:**

   ```
   - Ask 3-4 variable questions
   - Open "📜 Variable Chat Context"
   - Verify all questions listed
   - Verify variable IDs shown
   ```

3. **Clear Memory:**

   ```
   - Have a conversation
   - Click "Clear chat"
   - Verify context expander is empty/hidden
   - Ask new question
   - Verify fresh context starts
   ```

4. **Independence from Main Query:**
   ```
   Main: "Show Orleans Parish income"
   Variable Chat: "What poverty variables exist?"
   Main: "Now show poverty"
   → Main should still use Orleans (not affected by variable chat)
   ```

---

## Configuration

### Adjust Memory Size

In `init_session_state()`:

```python
# Default: 15 queries
st.session_state.variable_chat_memory = ConversationalMemory(max_history=15)

# Increase for longer memory:
st.session_state.variable_chat_memory = ConversationalMemory(max_history=25)
```

### Customize Context Display

In `_format_variable_chat_context()`:

```python
# Show more/fewer recent discussions
for i, ctx in enumerate(memory.history[-5:], 1):  # Change -5 to -10 for more
    ...

# Show more/fewer variable IDs
var_ids = ctx.variable_id.split(", ")[:3]  # Change :3 to :5 for more
```

---

## Summary

✅ **Implemented:**

- Separate LangChain memory for Variable Assistant
- Context viewer with collapsible expander
- Custom formatting for variable discussions
- Memory cleared with chat history

✅ **Benefits:**

- Natural follow-up questions about variables
- No interference with main query context
- Transparent memory display
- Easy reset

✅ **Ready to use!**

The Variable Assistant now has intelligent conversational memory that helps users explore Census variables naturally while keeping the main query interface's context separate and focused on data retrieval.
