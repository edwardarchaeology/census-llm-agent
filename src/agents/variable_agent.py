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
from docs.retriever import search_docs


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
            "reasoning": f"Best match with score {result.get('score', 0):.1f}/100",
            "doc_context": result.get("doc_context", [])
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


class VariableChatAgent(VariableResolverAgent):
    """Conversational assistant for explaining ACS variables."""
    
    def should_maintain_history(self) -> bool:
        """Keep chat history so follow-ups have context."""
        return True
    
    def answer_question(self, question: str, top_n: int = 5, year: int = 2023) -> Dict:
        """
        Generate a conversational answer about ACS variables.
        
        Args:
            question: User's natural-language question
            top_n: Number of candidate variables to include as context
            year: ACS vintage used for lookups
        
        Returns:
            Dict with:
                - answer: Markdown-formatted assistant response
                - candidates: Candidate variable metadata used for grounding
        """
        cleaned = question.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty.")
        
        # Detect metadata-style questions (e.g., "how many variables exist?")
        metadata_answer = self._maybe_answer_metadata(cleaned.lower(), year)
        if metadata_answer:
            return {
                "answer": metadata_answer,
                "candidates": [],
                "doc_snippets": []
            }
        
        general_answer = self._maybe_answer_general_topics(cleaned)
        if general_answer:
            return general_answer
        
        doc_snippets = self._merge_snippets(
            search_docs(cleaned, top_k=3)
        )
        doc_context = self._format_doc_context(doc_snippets)
        candidates = resolve_measure(cleaned, year=year, top_n=top_n)
        candidate_summary = self._format_chat_candidates(candidates)
        
        prompt = f"""You are helping an analyst understand which ACS variables are available.
The user asked: "{cleaned}"

Use the candidate variables and documentation excerpts below when helpful. Always mention the variable ID and cite which excerpt (if any) supports your answer. 
If the user's question is general, teach them how to find or reference variables in this system.

Candidate variables:
{candidate_summary}

Documentation excerpts:
{doc_context if doc_context else "No documentation snippets available."}

Respond with concise markdown (bullets are fine). Highlight the most relevant variable(s) and include any caveats (e.g., derived metrics, percentages vs. counts)."""
        
        response = self.call_llm(prompt)
        answer = response.get("content", "").strip()
        
        if not answer:
            answer = "I couldn't generate a response right now. Please try again after confirming Ollama is running."
        
        return {
            "answer": answer,
            "candidates": candidates,
            "doc_snippets": doc_snippets
        }
    
    def _maybe_answer_metadata(self, question_lower: str, year: int) -> Optional[str]:
        """
        Answer high-level ACS metadata questions directly instead of forcing a variable match.
        """
        if "variable" in question_lower and any(
            phrase in question_lower for phrase in ["how many", "number of", "count of"]
        ):
            catalog = get_census_variables_cached(year)
            total_vars = len(catalog)
            derived = len(DERIVED_METRICS)
            return (
                f"The ACS 5-year {year} dataset publishes about {total_vars:,} variables. "
                "Those include every base estimate, margin of error, and universe combination the Census Bureau exposes. "
                f"This app also defines {derived} derived metrics (ratios like poverty rate) on top of the raw variables. "
                "Ask about a topic—income, housing, demographics, etc.—and I'll highlight the most relevant variable IDs."
            )
        
        return None
    
    def _format_chat_candidates(self, candidates: List[Dict]) -> str:
        """Convert candidate metadata into a compact text block for the LLM."""
        if not candidates:
            return "No strong matches were found for this question."
        
        lines = []
        for idx, entry in enumerate(candidates, start=1):
            var_id = entry.get("variable_id", "UNKNOWN")
            label = entry.get("label", "Unknown label")
            concept = entry.get("concept") or "Concept unavailable"
            score = entry.get("score")
            is_derived = entry.get("is_derived", False)
            details = f"{idx}. {var_id} - {label} | Concept: {concept}"
            if score is not None:
                details += f" | Score: {score:.1f}"
            if is_derived:
                components = ", ".join(entry.get("variables", []))
                details += f" | Derived metric using: {components or 'N/A'}"
            lines.append(details)
        
        return "\n".join(lines)

    def _format_doc_context(self, snippets: List[Dict]) -> str:
        if not snippets:
            return ""
        lines = []
        for idx, snippet in enumerate(snippets, start=1):
            title = snippet.get("heading") or snippet.get("table_id") or snippet.get("source")
            text = snippet.get("text", "")
            lines.append(f"[{idx}] {title}: {text[:500]}")
        return "\n".join(lines)

    def _merge_snippets(self, *snippet_lists: List[List[Dict]]) -> List[Dict]:
        combined: List[Dict] = []
        seen = set()
        for snippets in snippet_lists:
            if not snippets:
                continue
            for snippet in snippets:
                text = snippet.get("text")
                if not text:
                    continue
                key = (snippet.get("source"), snippet.get("heading"), text[:120])
                if key in seen:
                    continue
                seen.add(key)
                combined.append(snippet)
        return combined

    def _maybe_answer_general_topics(self, question: str) -> Optional[Dict]:
        q_lower = question.lower()
        category_terms = ["category", "categories", "kind", "kinds", "type", "types", "topic", "topics"]
        general_terms = ["demographic", "demographics", "population", "data", "variables", "acs", "metrics"]
        ask_terms = ["what can i ask", "which", "what kinds", "what type", "what categories"]
        
        if not (
            (any(term in q_lower for term in category_terms) and any(term in q_lower for term in general_terms))
            or any(term in q_lower for term in ask_terms)
        ):
            return None
        
        doc_snippets = self._merge_snippets(
            search_docs(question, top_k=4),
            search_docs("ACS subject definitions categories", top_k=4),
            search_docs("ACS demographic subject areas", top_k=4)
        )
        
        if not doc_snippets:
            default_answer = (
                "The ACS lets you explore broad demographic categories such as population & age structure, "
                "race and Hispanic origin, household & family composition, education, income & poverty, "
                "employment, commuting, housing characteristics, health insurance, disability status, and veterans."
            )
            return {
                "answer": default_answer,
                "candidates": [],
                "doc_snippets": []
            }
        
        doc_context = self._format_doc_context(doc_snippets)
        prompt = f"""You are an ACS documentation assistant.
The user asked: "{question}"

Use the documentation excerpts below to summarize the major demographic/ACS subject categories they can explore.
Group related topics together (e.g., Population & Demographics, Income & Poverty, Housing, Education, Employment, Transportation, Health Insurance, Veteran/Disability).
For each category, give a short description and mention example variable types or tables. Reference excerpt numbers like [1], [2] when relevant.

Documentation excerpts:
{doc_context}

Respond with concise bullet points."""
        response = self.call_llm(prompt)
        answer = response.get("content", "").strip()
        if not answer:
            answer = (
                "Key ACS categories include population & age, race and ethnicity, households & families, "
                "education, income & poverty, employment, housing, commuting, health insurance, disability, "
                "and veteran status."
            )
        
        return {
            "answer": answer,
            "candidates": [],
            "doc_snippets": doc_snippets
        }
