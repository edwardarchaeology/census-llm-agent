"""
Census variable resolver agent - expert in ACS variables.
"""
import sys
import os
from typing import Dict, List, Optional
import pandas as pd

# Add single_agent to path for resolver import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'single_agent'))

from agents.base_agent import OllamaAgent
from agents.config import AGENT_CONFIGS
from resolver import DERIVED_METRICS, get_census_variables_cached, resolve_measure
from rapidfuzz import fuzz


class VariableResolverAgent(OllamaAgent):
    """Specialized agent for resolving census variables."""
    
    def __init__(self):
        config = AGENT_CONFIGS["variable_resolver"]
        super().__init__(
            model=config["model"],
            role=config["role"],
            temperature=config["temperature"]
        )
        self.derived_metrics = DERIVED_METRICS
        self.variable_catalog: Optional[pd.DataFrame] = None
    
    def get_system_prompt(self) -> str:
        """System prompt for variable resolver."""
        return """You are a US Census Bureau ACS (American Community Survey) variable expert.

Your expertise includes:
- Demographic variables (age, race, ethnicity, population)
- Economic variables (income, poverty, employment)
- Housing variables (ownership, rent, value)
- Social characteristics (education, language, disability)

Your job: Match user requests to specific ACS variable IDs or derived metrics.
Consider context, synonyms, and common phrasings.
Return confidence scores and reasoning for your selections."""
    
    def _load_catalog(self, year: int = 2023):
        """Lazy load the variable catalog."""
        if self.variable_catalog is None:
            self.variable_catalog = get_census_variables_cached(year)
    
    def resolve(self, measure: str, context: str = "", year: int = 2023) -> Dict:
        """
        Resolve measure to census variable(s).
        
        Args:
            measure: Measure name (e.g., "poverty rate", "median income")
            context: Full query context for disambiguation
            year: ACS year
            
        Returns:
            Dict with:
            - variable_id: Single ACS variable ID (or None if derived)
            - variables: List of variable IDs (for derived metrics)
            - label: Human-readable label
            - is_derived: Boolean
            - confidence: 0.0 to 1.0
            - reasoning: Explanation of selection
        """
        # Use the improved resolve_measure from single-agent resolver
        # It has better demographic filtering and scoring
        results = resolve_measure(measure, year=year, top_n=1)
        
        if not results:
            return {
                "variable_id": None,
                "variables": [],
                "label": measure,
                "is_derived": False,
                "confidence": 0.0,
                "reasoning": "No matching variables found in catalog"
            }
        
        result = results[0]
        
        # Convert to expected format
        return {
            "variable_id": result.get("variable_id"),
            "variables": result.get("variables", [result.get("variable_id")] if result.get("variable_id") else []),
            "label": result.get("label", measure),
            "is_derived": result.get("is_derived", False),
            "needs_area": result.get("needs_area", False),
            "formula": result.get("formula"),
            "confidence": min(result.get("score", 0) / 100.0, 1.0),  # Convert 0-100 score to 0-1
            "reasoning": f"Best match with score {result.get('score', 0):.1f}/100"
        }
    
    def _get_top_candidates(self, measure: str, top_k: int = 5) -> List[Dict]:
        """Use rapidfuzz to get top candidates from catalog."""
        if self.variable_catalog is None or self.variable_catalog.empty:
            return []
        
        scores = []
        for _, row in self.variable_catalog.iterrows():
            # Score against both label and concept
            label_score = fuzz.token_set_ratio(measure.lower(), row['label'].lower())
            concept_score = fuzz.token_set_ratio(measure.lower(), row.get('concept', '').lower())
            combined = max(label_score, concept_score)
            
            if combined > 40:  # Minimum threshold
                scores.append((combined, row))
        
        # Sort by score descending
        scores.sort(reverse=True, key=lambda x: x[0])
        
        return [
            {
                "variable_id": row['variable_id'],
                "label": row['label'],
                "concept": row.get('concept', ''),
                "score": score
            }
            for score, row in scores[:top_k]
        ]
    
    def _format_candidates(self, candidates: List[Dict]) -> str:
        """Format candidates for LLM prompt."""
        if not candidates:
            return "No candidates found."
        
        lines = []
        for i, c in enumerate(candidates, 1):
            lines.append(f"{i}. {c['variable_id']}: {c['label']}")
            lines.append(f"   Concept: {c['concept']}")
            lines.append(f"   Match Score: {c['score']:.1f}/100")
        
        return "\n".join(lines)
