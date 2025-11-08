"""
Query planner agent - decomposes complex queries into steps.
"""
from typing import List, Dict, Any
from agents.base_agent import OllamaAgent
from agents.config import AGENT_CONFIGS


class QueryPlannerAgent(OllamaAgent):
    """Agent that plans multi-step queries."""
    
    def __init__(self):
        config = AGENT_CONFIGS["query_planner"]
        super().__init__(
            model=config["model"],
            role=config["role"],
            temperature=config["temperature"]
        )
    
    def get_system_prompt(self) -> str:
        """System prompt for query planner."""
        return """You are a query planning expert for census data analysis.

Your expertise:
- Breaking complex queries into simple, atomic steps
- Understanding data operations: filter, sort, aggregate, compare, join
- Planning efficient execution sequences
- Handling multi-measure and multi-geography queries

Supported operations:
- FILTER: Apply conditions (e.g., poverty > 20%)
- TOP/BOTTOM: Get highest/lowest N values
- RANGE: Get values in a range
- AGGREGATE: Calculate averages, totals, etc.
- COMPARE: Compare values across geographies
- CORRELATE: Find relationships between measures

Your job: Create clear, executable plans."""
    
    def plan(self, query: str, initial_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create execution plan for a query.
        
        Args:
            query: Natural language query
            initial_intent: Basic intent extracted by orchestrator
            
        Returns:
            Dict with:
            - complexity: "simple" or "complex"
            - steps: List of execution steps
            - reasoning: Explanation of the plan
        """
        # Determine if query is complex
        is_complex = self._is_complex_query(query)
        
        if not is_complex:
            return {
                "complexity": "simple",
                "steps": [{
                    "step": 1,
                    "action": initial_intent.get("task", "filter"),
                    "description": "Single-step query execution"
                }],
                "reasoning": "Query can be executed in a single step"
            }
        
        # Complex query - ask LLM to plan
        prompt = f"""Plan execution for this complex query:
"{query}"

Initial intent: {initial_intent}

Create a step-by-step execution plan.

Examples:

Query: "Compare poverty rates in New Orleans and Baton Rouge"
Plan:
1. Fetch poverty rate data for Orleans Parish (FIPS: 071)
2. Fetch poverty rate data for East Baton Rouge Parish (FIPS: 033)
3. Calculate average poverty rate for each parish
4. Compare the two averages
5. Return comparison result

Query: "Show tracts with high income AND low poverty in Caddo"
Plan:
1. Fetch median income for Caddo Parish tracts
2. Filter tracts with income > $75,000
3. Fetch poverty rate for those filtered tracts
4. Filter tracts with poverty < 10%
5. Return intersection of both conditions

Return JSON:
{{
  "complexity": "complex",
  "steps": [
    {{"step": 1, "action": "fetch", "measure": "poverty rate", "geography": "Orleans Parish"}},
    {{"step": 2, "action": "aggregate", "operation": "mean"}},
    ...
  ],
  "reasoning": "Query requires multiple geographies and comparison"
}}
"""
        
        result = self.call_llm(prompt, format="json")
        return result
    
    def _is_complex_query(self, query: str) -> bool:
        """Determine if query requires multi-step planning."""
        complexity_indicators = [
            # Comparison keywords
            "compare", "versus", "vs", "vs.", "difference between",
            # Multiple conditions
            " and ", " or ", "both", "either",
            # Aggregation keywords
            "average", "mean", "total", "sum", "aggregate", "across",
            # Correlation keywords
            "relationship", "correlation", "correlated with",
            # Multiple geographies
            "parishes", "cities", "counties",
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in complexity_indicators)
    
    def validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a plan is executable.
        
        Returns:
            Dict with:
            - valid: Boolean
            - issues: List of validation issues
        """
        issues = []
        
        if not plan.get("steps"):
            issues.append("Plan has no steps")
        
        # Check that steps are numbered sequentially
        steps = plan.get("steps", [])
        for i, step in enumerate(steps, 1):
            if step.get("step") != i:
                issues.append(f"Step numbering error: expected {i}, got {step.get('step')}")
        
        # Check that each step has required fields
        for step in steps:
            if "action" not in step:
                issues.append(f"Step {step.get('step', '?')} missing 'action' field")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
