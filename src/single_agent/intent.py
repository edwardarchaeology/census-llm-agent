"""
Intent extraction from natural language using Ollama.
"""
import json
import os
import re
import sys
from typing import Optional

import requests
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from geography import resolve_geography

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")

# Word to number mapping
WORD_TO_NUMBER = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "fifteen": 15, "twenty": 20, "thirty": 30, "fifty": 50, "hundred": 100
}


class Geography(BaseModel):
    """Geography specification."""
    state: str = "22"  # Louisiana FIPS
    county_fips: Optional[str] = None


class Intent(BaseModel):
    """Parsed intent from natural language query."""
    task: str = Field(..., description="One of: top, bottom, filter, range")
    measure: str = Field(..., description="The measure/metric to query")
    op: Optional[str] = Field(None, description="Operator for filter: >=, <=, >, <, =")
    value: Optional[float] = Field(None, description="Value for filter or comparison")
    range_min: Optional[float] = Field(None, description="Minimum for range queries")
    range_max: Optional[float] = Field(None, description="Maximum for range queries")
    limit: Optional[int] = Field(None, description="Number of results for top/bottom")
    sort: Optional[str] = Field(None, description="Sort order: asc or desc")
    geography: Geography = Field(default_factory=Geography)


def normalize_value(text: str) -> Optional[float]:
    """
    Normalize value strings like '20%', '35k', '1.5m', 'ten' to numbers.
    """
    text = text.strip().lower()
    
    # Check for word numbers
    if text in WORD_TO_NUMBER:
        return float(WORD_TO_NUMBER[text])
    
    # Remove commas
    text = text.replace(",", "")
    
    # Check for percentage
    if "%" in text:
        num_str = text.replace("%", "").strip()
        try:
            return float(num_str) / 100.0
        except ValueError:
            return None
    
    # Check for k/m suffixes
    multiplier = 1
    if text.endswith("k"):
        multiplier = 1000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1000000
        text = text[:-1]
    
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def extract_city_county(question: str) -> Optional[str]:
    """Extract county FIPS from geographic mentions in the question."""
    question_lower = question.lower()
    
    # Try to extract any Louisiana parish or city mentioned
    # Use the comprehensive geography module
    words = question_lower.split()
    
    # Try multi-word combinations first (e.g., "New Orleans", "East Baton Rouge")
    for i in range(len(words)):
        for j in range(i + 4, i, -1):  # Try up to 4-word combinations
            phrase = " ".join(words[i:j])
            _, county_fips = resolve_geography(phrase)
            if county_fips:
                return county_fips
    
    return None


def build_few_shot_prompt(question: str) -> str:
    """Build few-shot prompt with examples."""
    # Use double braces to escape them in the string, then format only the question
    prompt = f"""You are a query intent parser for Louisiana census tract data.
Extract structured intent from natural language questions about census data.

Return ONLY valid JSON matching this schema:
{{
  "task": "top|bottom|filter|range",
  "measure": "the measure name",
  "op": ">=|<=|>|<|=" (for filter only),
  "value": numeric value (for filter),
  "range_min": number (for range),
  "range_max": number (for range),
  "limit": number (for top/bottom),
  "sort": "asc|desc" (OPTIONAL - omit to use default)
}}

IMPORTANT RULES:
- "top" means HIGHEST values (sort: desc) - omit "sort" field to use default
- "bottom" means LOWEST values (sort: asc) - omit "sort" field to use default
- "top X by poverty rate" means X tracts with HIGHEST poverty (desc)
- "lowest X by poverty rate" means X tracts with LOWEST poverty (asc)

Examples:

Q: "What tract has the highest median income in New Orleans?"
A: {{"task": "top", "measure": "median income", "limit": 1}}

Q: "Give me all tracts with 20% or more African Americans"
A: {{"task": "filter", "measure": "african american share", "op": ">=", "value": 0.2}}

Q: "lowest 5 poverty rate tracts in Lafayette"
A: {{"task": "bottom", "measure": "poverty rate", "limit": 5}}

Q: "top 10 population density tracts"
A: {{"task": "top", "measure": "population density", "limit": 10}}

Q: "top 5 tracts by poverty rate in Caddo Parish"
A: {{"task": "top", "measure": "poverty rate", "limit": 5}}

Q: "median income between 40k and 75k"
A: {{"task": "range", "measure": "median income", "range_min": 40000, "range_max": 75000}}

Q: "income under 35k in Baton Rouge"
A: {{"task": "filter", "measure": "median income", "op": "<", "value": 35000}}

Q: "tracts with poverty rate under 10%"
A: {{"task": "filter", "measure": "poverty rate", "op": "<", "value": 10}}

Q: "poverty rate over 40 percent"
A: {{"task": "filter", "measure": "poverty rate", "op": ">", "value": 40}}

Now extract intent from this question:
Q: "{question}"
A: """
    
    return prompt


def call_ollama(prompt: str) -> dict:
    """Call Ollama API with the prompt."""
    url = f"{OLLAMA_ENDPOINT}/api/chat"
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        message_content = result.get("message", {}).get("content", "{}")
        return json.loads(message_content)
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama API call failed: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Ollama response as JSON: {e}")


def normalize_intent(raw_intent: dict, question: str) -> Intent:
    """
    Normalize and validate raw intent from LLM.
    Apply defaults, normalize values, extract geography.
    """
    # Set defaults
    task = raw_intent.get("task", "filter")
    
    # Default sort based on task
    sort = raw_intent.get("sort")
    if not sort:
        if task == "top":
            sort = "desc"
        elif task == "bottom":
            sort = "asc"
        else:
            sort = "desc"
    
    # Default limit for top/bottom
    limit = raw_intent.get("limit")
    if task in ["top", "bottom"] and not limit:
        limit = 10
    
    # Normalize value if present
    value = raw_intent.get("value")
    if value is not None and isinstance(value, str):
        value = normalize_value(value)
    
    # Normalize range values
    range_min = raw_intent.get("range_min")
    range_max = raw_intent.get("range_max")
    if range_min is not None and isinstance(range_min, str):
        range_min = normalize_value(range_min)
    if range_max is not None and isinstance(range_max, str):
        range_max = normalize_value(range_max)
    
    # Extract geography
    county_fips = extract_city_county(question)
    geography = Geography(state="22", county_fips=county_fips)
    
    # Build intent object
    intent = Intent(
        task=task,
        measure=raw_intent.get("measure", "population"),
        op=raw_intent.get("op"),
        value=value,
        range_min=range_min,
        range_max=range_max,
        limit=limit,
        sort=sort,
        geography=geography
    )
    
    return intent


def extract_intent(question: str) -> Intent:
    """
    Main entry point: extract structured intent from natural language question.
    """
    prompt = build_few_shot_prompt(question)
    raw_intent = call_ollama(prompt)
    intent = normalize_intent(raw_intent, question)
    return intent
