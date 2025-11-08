"""
Multi-agent system for census data analysis.
"""
from agents.base_agent import OllamaAgent
from agents.geography_agent import GeographyAgent
from agents.variable_agent import VariableResolverAgent, VariableChatAgent
from agents.query_planner_agent import QueryPlannerAgent
from agents.orchestrator_agent import OrchestratorAgent

__all__ = [
    "OllamaAgent",
    "GeographyAgent",
    "VariableResolverAgent",
    "VariableChatAgent",
    "QueryPlannerAgent",
    "OrchestratorAgent",
]
