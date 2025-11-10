"""
LangChain-enhanced Census query interface.
Combines RAG, conversational memory, and agent tools.
"""
import sys
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "single_agent"))
sys.path.insert(0, str(project_root / "src" / "langchain_features"))

from conversation_memory import ConversationalMemory, QueryContext
from census_rag import CensusVariableRAG
from single_agent.mvp import run_query as run_single_agent_query
from resolver import resolve_measure


class LangChainQueryEngine:
    """
    Enhanced query engine with LangChain features.
    
    Features:
    - Conversational memory for follow-up questions
    - RAG for better variable selection
    - Context-aware query augmentation
    """
    
    def __init__(self):
        self.memory = ConversationalMemory(max_history=10)
        self.rag = None  # Lazy load
        self._rag_enabled = True
    
    def _ensure_rag(self):
        """Lazy load RAG system."""
        if self.rag is None and self._rag_enabled:
            try:
                self.rag = CensusVariableRAG()
                print("✅ RAG system loaded")
            except Exception as e:
                print(f"⚠️  RAG system unavailable: {e}")
                self._rag_enabled = False
    
    def process_query(
        self,
        query: str,
        mode: str = "single",
        verbose: bool = False,
        use_memory: bool = True,
        use_rag: bool = True
    ) -> Dict:
        """
        Process a query with LangChain enhancements.
        
        Args:
            query: User's natural language query
            mode: 'single' or 'multi' agent mode
            verbose: Whether to show detailed output
            use_memory: Use conversational memory
            use_rag: Use RAG for variable selection
            
        Returns:
            Dict with:
            - dataframe: Results dataframe
            - label: Human-readable label
            - is_follow_up: Whether this was a follow-up question
            - inferred_context: Context inferred from history
            - rag_context: RAG-augmented context (if enabled)
            - conversation_summary: Conversation history summary
        """
        result = {
            "is_follow_up": False,
            "inferred_context": {},
            "rag_context": None,
            "conversation_summary": None
        }
        
        # Check if follow-up question
        if use_memory and self.memory.is_follow_up(query):
            result["is_follow_up"] = True
            result["inferred_context"] = self.memory.infer_missing_context(query)
            result["conversation_summary"] = self.memory.get_context_summary()
            
            if verbose:
                print("\n🔄 Detected follow-up question")
                print(f"Inferred context: {result['inferred_context']}")
        
        # Augment query with RAG context
        if use_rag:
            self._ensure_rag()
            if self.rag:
                # Use search_variables_only for backward compatibility with existing code
                rag_matches = self.rag.search_variables_only(query, top_k=3)
                result["rag_context"] = rag_matches
                
                if verbose and rag_matches:
                    print("\n📚 RAG-suggested variables:")
                    for match in rag_matches[:3]:
                        print(f"  - {match['variable_id']}: {match['label']} (score: {match['score']:.2f})")
        
        # Execute query
        try:
            result_df = run_single_agent_query(query, return_debug_info=True)
            
            # Extract metadata for memory
            label = result_df.attrs.get("label", "Census Data")
            debug_info = result_df.attrs.get("debug_info", {})
            
            # Add to conversation memory
            if use_memory:
                geography_info = debug_info.get("geography", {})
                resolved_info = debug_info.get("resolved", {})
                
                self.memory.add_query(
                    query=query,
                    parish=geography_info.get("parish_name"),
                    county_fips=geography_info.get("county_fips"),
                    measure=resolved_info.get("measure"),
                    variable_id=resolved_info.get("variable_id"),
                    result_count=len(result_df),
                    successful=True
                )
            
            # Package results
            result.update({
                "dataframe": result_df,
                "label": label,
                "debug_info": debug_info,
                "success": True
            })
            
        except Exception as e:
            result.update({
                "dataframe": None,
                "error": str(e),
                "success": False
            })
            
            # Record failed query in memory
            if use_memory:
                self.memory.add_query(
                    query=query,
                    successful=False
                )
        
        return result
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        return self.memory.get_context_summary()
    
    def clear_memory(self):
        """Clear conversation history."""
        self.memory.clear()
    
    def get_rag_suggestions(self, query: str, top_k: int = 5):
        """Get RAG variable suggestions (variables only, for UI)."""
        self._ensure_rag()
        if self.rag:
            return self.rag.search_variables_only(query, top_k=top_k)
        return []
    
    def get_rag_documentation(self, query: str, top_k: int = 3):
        """Get RAG documentation matches (PDFs and Excel files)."""
        self._ensure_rag()
        if self.rag:
            all_results = self.rag.search(query, top_k=top_k * 2)
            # Filter to only documentation (not variables)
            return [r for r in all_results if r.get("doc_type") in ["pdf", "excel"]][:top_k]
        return []


# Example usage
if __name__ == "__main__":
    print("Testing LangChain Query Engine\n")
    
    engine = LangChainQueryEngine()
    
    # Test conversation flow
    queries = [
        "What are the top 5 census tracts in Orleans Parish by median income?",
        "Now show me the poverty rate",
        "What about Lafayette Parish instead?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print('='*60)
        
        result = engine.process_query(query, verbose=True)
        
        if result.get("success"):
            df = result["dataframe"]
            print(f"\n✅ Results: {result['label']}")
            print(f"Found {len(df)} tracts")
            print(f"Is follow-up: {result['is_follow_up']}")
        else:
            print(f"\n❌ Error: {result.get('error')}")
