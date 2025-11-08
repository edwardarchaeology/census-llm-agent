"""
Orchestrator agent - coordinates all other agents.
"""
from typing import Dict, Any, Optional
from agents.base_agent import OllamaAgent
from agents.config import AGENT_CONFIGS
from agents.geography_agent import GeographyAgent
from agents.variable_agent import VariableResolverAgent
from agents.query_planner_agent import QueryPlannerAgent


class OrchestratorAgent(OllamaAgent):
    """Main orchestrator that coordinates specialized agents."""
    
    def __init__(self):
        config = AGENT_CONFIGS["orchestrator"]
        super().__init__(
            model=config["model"],
            role=config["role"],
            temperature=config["temperature"]
        )
        
        # Initialize specialized agents
        self.geography_agent = GeographyAgent()
        self.variable_agent = VariableResolverAgent()
        self.planner_agent = QueryPlannerAgent()
        
        print(f">>> Orchestrator initialized with {config['model']}")
        print(f"    - Geography Agent: {self.geography_agent.model}")
        print(f"    - Variable Agent: {self.variable_agent.model}")
        print(f"    - Query Planner: {self.planner_agent.model}")
    
    def get_system_prompt(self) -> str:
        """System prompt for orchestrator."""
        return """You are the orchestrator of a census data analysis system.

Your responsibilities:
- Coordinate specialized agents (Geography, Variable Resolver, Query Planner)
- Extract basic intent from user queries
- Make high-level decisions about query execution
- Handle errors gracefully
- Maintain conversation context for follow-up questions

You have access to:
- Geography Agent: Resolves Louisiana parishes and cities
- Variable Resolver Agent: Matches measures to Census variables
- Query Planner Agent: Decomposes complex queries

Your job: Understand the user's intent and coordinate agents to fulfill it."""
    
    def should_maintain_history(self) -> bool:
        """Orchestrator maintains conversation history for follow-ups."""
        return True
    
    def process_query(self, question: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Main entry point - process a user query through the agent system.
        
        Args:
            question: Natural language query
            verbose: Whether to print detailed progress
            
        Returns:
            Dict with:
            - intent: Extracted intent
            - geography: Geography information
            - variable: Variable resolution
            - plan: Execution plan
            - execution_type: "simple" or "complex"
        """
        if verbose:
            print(f"\n>>> Orchestrator: Processing query...")
        
        # Step 1: Extract basic intent
        intent = self._extract_basic_intent(question)
        if verbose:
            print(f">>> Initial intent: {intent['task']} / {intent['measure']}")
        
        # Step 2: Resolve geography (via Geography Agent)
        parish, fips, geo_confidence = self.geography_agent.resolve(question)
        if verbose:
            geography_str = f"{parish} (FIPS: {fips})" if parish else "All Louisiana"
            print(f">>> Geography: {geography_str} (confidence: {geo_confidence:.2f})")
        
        # Step 3: Resolve variable (via Variable Resolver Agent)
        variable_result = self.variable_agent.resolve(
            measure=intent['measure'],
            context=question
        )
        if verbose:
            var_type = "DERIVED" if variable_result['is_derived'] else variable_result.get('variable_id', 'UNKNOWN')
            print(f">>> Variable: {var_type}")
            print(f"    Label: {variable_result['label']}")
            print(f"    Confidence: {variable_result['confidence']:.2f}")
        
        # Step 4: Check if we need clarification
        if variable_result['confidence'] < 0.6:
            if verbose:
                print(f">>> WARNING: Low confidence ({variable_result['confidence']:.2f})")
                print(f"    Reasoning: {variable_result.get('reasoning', 'Unknown')}")
        
        # Step 5: Create execution plan (via Query Planner Agent)
        plan = self.planner_agent.plan(question, intent)
        if verbose:
            print(f">>> Query complexity: {plan['complexity']}")
            if plan['complexity'] == 'complex':
                print(f"    Plan has {len(plan.get('steps', []))} steps")
        
        # Step 6: Package results
        result = {
            "intent": intent,
            "geography": {
                "parish": parish,
                "fips": fips,
                "confidence": geo_confidence
            },
            "variable": variable_result,
            "plan": plan,
            "execution_type": plan['complexity'],
            "status": "ready"
        }
        
        return result
    
    def _extract_basic_intent(self, question: str) -> Dict[str, Any]:
        """Extract basic intent using orchestrator's LLM."""
        prompt = f"""Extract basic query intent from this question:
"{question}"

Identify:
- Task type: top, bottom, filter, range, compare, aggregate
- What to measure (the metric/variable)
- Any numeric values or thresholds
- Number of results (limit)
- Comparison operators for filter tasks

Return JSON:
{{
  "task": "top|bottom|filter|range|compare|aggregate",
  "measure": "what to measure",
  "value": numeric threshold or null,
  "limit": number of results or null,
  "op": ">=|<=|>|<|=" or null
}}

IMPORTANT: For filter tasks, extract the operator precisely:
- "over", "above", "more than", "greater than" → op: ">"
- "at least", "or more" → op: ">="
- "under", "below", "less than" → op: "<"
- "at most", "or less" → op: "<="
- "exactly", "equal to" → op: "="

Examples:
- "top 5 poverty rate" → {{"task": "top", "measure": "poverty rate", "limit": 5}}
- "income over 50k" → {{"task": "filter", "measure": "income", "value": 50000, "op": ">"}}
- "poverty rate under 10%" → {{"task": "filter", "measure": "poverty rate", "value": 10, "op": "<"}}
- "tracts with 20% or more African Americans" → {{"task": "filter", "measure": "african american share", "value": 20, "op": ">="}}
- "compare New Orleans and Baton Rouge" → {{"task": "compare", "measure": "unspecified"}}
"""
        
        result = self.call_llm(prompt, format="json")
        
        # Normalize and add defaults
        if not result.get("task"):
            result["task"] = "filter"
        if not result.get("measure"):
            result["measure"] = "population"
        
        return result
    
    def ask_clarification(self, variable_result: Dict[str, Any]) -> str:
        """
        Generate clarification question for ambiguous requests.
        
        Args:
            variable_result: Result from variable resolver with low confidence
            
        Returns:
            Clarification question string
        """
        return f"""I found multiple possible interpretations for your request:

Measure: {variable_result.get('label', 'Unknown')}
Confidence: {variable_result.get('confidence', 0.0):.0%}

{variable_result.get('reasoning', 'No additional context available.')}

Could you be more specific about what you're looking for?"""
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents in the system."""
        return {
            "orchestrator": self.get_info(),
            "geography_agent": self.geography_agent.get_info(),
            "variable_agent": self.variable_agent.get_info(),
            "planner_agent": self.planner_agent.get_info()
        }
