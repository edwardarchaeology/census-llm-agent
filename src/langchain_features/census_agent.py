"""
LangChain Agent for Census Data Queries.
Uses ReAct pattern with tools for autonomous query handling.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain import hub
from langchain_core.prompts import PromptTemplate

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "single_agent"))

from resolver import resolve_measure, clean_census_label
from geography import resolve_geography
from single_agent.mvp import run_query as run_single_agent_query


class CensusQueryAgent:
    """
    LangChain agent that can query Census data using tools.
    Replaces manual single/multi-agent switching with intelligent tool use.
    """
    
    def __init__(self, model: str = "phi3:mini", temperature: float = 0.1):
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.tools = self._create_tools()
        self.agent = None
        self.agent_executor = None
        self._setup_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent."""
        
        def resolve_geography_tool(query: str) -> str:
            """Identify Louisiana parish from query."""
            try:
                result = resolve_geography(query)
                if result and result[0]:
                    parish, fips, _ = result
                    return f"Parish: {parish}, FIPS: {fips}"
                return "No parish identified in query"
            except Exception as e:
                return f"Error resolving geography: {e}"
        
        def resolve_variable_tool(measure: str) -> str:
            """Find Census variable for a measure."""
            try:
                results = resolve_measure(measure, top_n=1)
                if results:
                    result = results[0]
                    var_id = result.get('variable_id')
                    label = result.get('label')
                    desc = result.get('description', '')
                    return f"Variable: {var_id}\nLabel: {label}\nDescription: {desc}"
                return "No matching variable found"
            except Exception as e:
                return f"Error resolving variable: {e}"
        
        def query_census_data_tool(query: str) -> str:
            """Execute a Census data query and return results."""
            try:
                import pandas as pd
                result_df = run_single_agent_query(query, return_debug_info=True)
                
                if result_df is None or len(result_df) == 0:
                    return "No results found"
                
                # Format results
                label = result_df.attrs.get("label", "Census Data")
                output = [f"Query Results: {label}"]
                output.append(f"Found {len(result_df)} census tracts\n")
                
                # Show top 5 results
                top_5 = result_df.head(5)
                for idx, row in top_5.iterrows():
                    name = row.get('tract_name', row.get('NAME', 'Unknown'))
                    value = row.get('value', 'N/A')
                    output.append(f"  - {name}: {value}")
                
                return "\n".join(output)
                
            except Exception as e:
                return f"Error querying Census data: {e}"
        
        def list_available_parishes_tool(input: str = "") -> str:
            """List available Louisiana parishes."""
            from geography import LOUISIANA_PARISHES
            parishes = [p.replace(" parish", "").title() for p in LOUISIANA_PARISHES.keys() 
                       if " parish" in p.lower()]
            parishes = sorted(set(parishes))[:20]  # Top 20 for brevity
            return "Available Louisiana parishes:\n" + "\n".join(f"  - {p}" for p in parishes)
        
        tools = [
            Tool(
                name="resolve_geography",
                func=resolve_geography_tool,
                description="Identifies Louisiana parish from a natural language query. "
                           "Use this to find which parish the user is asking about. "
                           "Input: query string, Output: parish name and FIPS code"
            ),
            Tool(
                name="resolve_variable",
                func=resolve_variable_tool,
                description="Finds the Census variable for a measure like 'median income', 'poverty rate', etc. "
                           "Use this to identify which Census variable to query. "
                           "Input: measure name, Output: variable ID and description"
            ),
            Tool(
                name="query_census_data",
                func=query_census_data_tool,
                description="Executes a Census data query and returns results for census tracts. "
                           "Use this to get actual data after identifying parish and variable. "
                           "Input: natural language query, Output: formatted results with tract names and values"
            ),
            Tool(
                name="list_parishes",
                func=list_available_parishes_tool,
                description="Lists available Louisiana parishes. "
                           "Use this when user asks what parishes are available or misspells a parish name. "
                           "Input: empty string, Output: list of parish names"
            )
        ]
        
        return tools
    
    def _setup_agent(self):
        """Setup the ReAct agent."""
        
        # Custom prompt template for Census queries
        template = """You are a helpful assistant for querying US Census data for Louisiana.
You have access to tools that can help you answer questions about census tracts.

Available tools:
{tools}

Tool names: {tool_names}

When answering questions:
1. First identify what parish/parishes the user is asking about
2. Identify what measure they want (income, poverty, population, etc.)
3. Query the data using the appropriate tools
4. Present results clearly

Always use tools when needed. Think step by step.

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )
        
        # Create agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def query(self, question: str) -> str:
        """
        Execute a query using the agent.
        
        Args:
            question: Natural language query
            
        Returns:
            Agent's response
        """
        try:
            result = self.agent_executor.invoke({"input": question})
            return result.get("output", "No response generated")
        except Exception as e:
            return f"Error executing query: {e}"


# Test the agent
if __name__ == "__main__":
    print("Initializing Census Query Agent...\n")
    
    agent = CensusQueryAgent()
    
    test_queries = [
        "What are the top 5 census tracts in Orleans Parish by median income?",
        "Show me poverty rates in Lafayette Parish",
        "What parishes are available?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        response = agent.query(query)
        print(f"\nResponse:\n{response}")
