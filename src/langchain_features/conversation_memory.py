"""
Conversational Memory for Census Data Explorer.
Enables follow-up questions and context-aware queries.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class QueryContext:
    """Context from a previous query."""
    query: str
    timestamp: datetime
    parish: Optional[str] = None
    county_fips: Optional[str] = None
    measure: Optional[str] = None
    variable_id: Optional[str] = None
    result_count: int = 0
    successful: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "timestamp": self.timestamp.isoformat(),
            "parish": self.parish,
            "county_fips": self.county_fips,
            "measure": self.measure,
            "variable_id": self.variable_id,
            "result_count": self.result_count,
            "successful": self.successful
        }


class ConversationalMemory:
    """
    Manages conversation history and context for follow-up questions.
    
    Features:
    - Tracks previous queries and results
    - Identifies follow-up patterns ("now show", "what about", "also")
    - Carries forward geographic and measure context
    - Provides context summaries for LLM
    """
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[QueryContext] = []
        self.current_context: Optional[QueryContext] = None
    
    def add_query(self, query: str, **kwargs):
        """
        Add a query to history.
        
        Args:
            query: The user's query
            **kwargs: Context fields (parish, measure, variable_id, etc.)
        """
        context = QueryContext(
            query=query,
            timestamp=datetime.now(),
            **kwargs
        )
        
        self.history.append(context)
        self.current_context = context
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_last_context(self) -> Optional[QueryContext]:
        """Get the most recent query context."""
        return self.current_context
    
    def is_follow_up(self, query: str) -> bool:
        """
        Detect if query is a follow-up question.
        
        Follow-up patterns:
        - "Now show me..."
        - "What about..."
        - "Also include..."
        - "Instead of..."
        - Starts with conjunction or reference word
        """
        query_lower = query.lower().strip()
        
        follow_up_patterns = [
            "now ", "also ", "what about", "how about",
            "instead of", "compared to", "and ", "but ",
            "same for", "for that", "those", "them",
            "the same"
        ]
        
        return any(query_lower.startswith(pattern) for pattern in follow_up_patterns)
    
    def get_context_summary(self) -> str:
        """
        Get formatted summary of conversation context for LLM.
        
        Returns:
            String summary of previous queries and context
        """
        if not self.history:
            return "No previous conversation history."
        
        summary_parts = ["Previous Conversation Context:"]
        
        # Show last 3 queries
        recent = self.history[-3:]
        for i, ctx in enumerate(reversed(recent), 1):
            parts = [f"\n{i}. Query: \"{ctx.query}\""]
            
            if ctx.parish:
                parts.append(f"   Geography: {ctx.parish} (FIPS: {ctx.county_fips})")
            
            if ctx.measure:
                parts.append(f"   Measure: {ctx.measure}")
                if ctx.variable_id:
                    parts.append(f"   Variable: {ctx.variable_id}")
            
            if ctx.result_count > 0:
                parts.append(f"   Results: {ctx.result_count} tracts")
            
            summary_parts.append("\n".join(parts))
        
        # Add current context if available
        if self.current_context:
            summary_parts.append("\nCurrent Context:")
            if self.current_context.parish:
                summary_parts.append(f"  - Working with: {self.current_context.parish}")
            if self.current_context.measure:
                summary_parts.append(f"  - Last measure: {self.current_context.measure}")
        
        return "\n".join(summary_parts)
    
    def infer_missing_context(self, query: str) -> Dict:
        """
        Infer missing parameters from conversation history.
        
        Args:
            query: Current query
            
        Returns:
            Dict with inferred parish, measure, etc.
        """
        inferred = {}
        
        if not self.current_context:
            return inferred
        
        query_lower = query.lower()
        
        # If query doesn't mention a parish, use previous one
        # Check for parish mentions
        has_parish_mention = any(word in query_lower for word in [
            "parish", "orleans", "caddo", "lafayette", "jefferson",
            "east baton rouge", "st.", "saint"
        ])
        
        if not has_parish_mention and self.current_context.parish:
            inferred['parish'] = self.current_context.parish
            inferred['county_fips'] = self.current_context.county_fips
        
        # If query doesn't mention a measure but refers to "it", "that", "them"
        reference_words = ["it", "that", "those", "them", "same", "also"]
        has_reference = any(word in query_lower for word in reference_words)
        
        # Check if query mentions a new measure
        has_measure_mention = any(word in query_lower for word in [
            "income", "poverty", "population", "density", "rate",
            "median", "average", "total", "percentage"
        ])
        
        if has_reference and not has_measure_mention and self.current_context.measure:
            inferred['measure'] = self.current_context.measure
            inferred['variable_id'] = self.current_context.variable_id
        
        return inferred
    
    def get_history_json(self) -> str:
        """Get conversation history as JSON string."""
        return json.dumps([ctx.to_dict() for ctx in self.history], indent=2)
    
    def clear(self):
        """Clear conversation history."""
        self.history.clear()
        self.current_context = None


# Example usage
if __name__ == "__main__":
    memory = ConversationalMemory()
    
    # Simulate conversation
    print("Testing Conversational Memory\n")
    
    # First query
    memory.add_query(
        "What are the top 5 census tracts in Orleans Parish by median income?",
        parish="Orleans Parish",
        county_fips="071",
        measure="median income",
        variable_id="B19013_001E",
        result_count=5,
        successful=True
    )
    
    print("Query 1:")
    print(memory.get_context_summary())
    
    # Follow-up query
    follow_up = "Now show me the poverty rate"
    print(f"\n\nQuery 2: '{follow_up}'")
    print(f"Is follow-up? {memory.is_follow_up(follow_up)}")
    
    inferred = memory.infer_missing_context(follow_up)
    print(f"Inferred context: {inferred}")
    
    memory.add_query(
        follow_up,
        parish=inferred.get('parish', 'Orleans Parish'),
        county_fips=inferred.get('county_fips', '071'),
        measure="poverty rate",
        variable_id="DERIVED",
        result_count=5,
        successful=True
    )
    
    print("\nUpdated context:")
    print(memory.get_context_summary())
