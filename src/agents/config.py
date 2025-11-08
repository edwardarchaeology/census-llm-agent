"""
Agent configuration for multi-agent system.
All agents use phi3:mini for simplicity and efficiency.
"""
import os

AGENT_CONFIGS = {
    "orchestrator": {
        "model": os.getenv("ORCHESTRATOR_MODEL", "phi3:mini"),
        "temperature": 0.2,
        "role": "Main coordinator and decision maker"
    },
    "geography": {
        "model": os.getenv("GEOGRAPHY_MODEL", "phi3:mini"),
        "temperature": 0.0,  # Deterministic for geography
        "role": "Louisiana geography specialist"
    },
    "variable_resolver": {
        "model": os.getenv("VARIABLE_MODEL", "phi3:mini"),
        "temperature": 0.2,
        "role": "Census variable resolver"
    },
    "query_planner": {
        "model": os.getenv("PLANNER_MODEL", "phi3:mini"),
        "temperature": 0.3,
        "role": "Query planning and decomposition"
    },
    "validator": {
        "model": os.getenv("VALIDATOR_MODEL", "phi3:mini"),
        "temperature": 0.1,
        "role": "Result validation"
    }
}

# Ollama endpoint
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
