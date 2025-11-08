"""Test the multi-agent orchestrator directly."""
import sys
sys.path.insert(0, 'src')

from agents.orchestrator_agent import OrchestratorAgent

print("Testing Multi-Agent Orchestrator...")
print("=" * 60)

try:
    # Initialize orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = OrchestratorAgent()
    print("✅ Orchestrator initialized")
    
    # Test query
    print("\n2. Testing query processing...")
    question = "What are the top 5 census tracts in Orleans Parish by median income?"
    print(f"Query: {question}")
    
    result = orchestrator.process_query(question, verbose=True)
    
    print("\n✅ Query processed successfully!")
    print(f"\nResult summary:")
    print(f"  - Task: {result['intent'].get('task')}")
    print(f"  - Measure: {result['intent'].get('measure')}")
    print(f"  - Limit: {result['intent'].get('limit')}")
    print(f"  - Geography: {result['geography'].get('parish')} (FIPS: {result['geography'].get('fips')})")
    print(f"  - Variable: {result['variable'].get('label')}")
    print(f"  - Execution type: {result['execution_type']}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 60)
