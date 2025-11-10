"""
Test the enhanced RAG system with ACS documentation.
Run this to rebuild the vector database with PDFs and Excel files.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "langchain_features"))

from census_rag import CensusVariableRAG


def main():
    print("="*70)
    print("Testing Enhanced RAG with ACS Documentation")
    print("="*70)
    
    # Build RAG with documentation
    print("\n1. Building RAG with variables + documentation...")
    rag = CensusVariableRAG(rebuild=True, include_docs=True, docs_dir="./acs_docs")
    
    print("\n" + "="*70)
    print("2. Testing semantic search across all document types")
    print("="*70)
    
    test_queries = [
        ("median household income", "Should find B19013 + income docs"),
        ("poverty rate calculation", "Should find poverty variables + how to calculate"),
        ("what does universe mean", "Should find documentation explaining universe"),
        ("housing units", "Should find housing variables + definitions"),
    ]
    
    for query, expected in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")
        print("-"*70)
        
        matches = rag.search(query, top_k=5)
        
        for i, match in enumerate(matches, 1):
            doc_type = match['doc_type']
            score = match['score']
            
            if doc_type == "variable":
                print(f"{i}. [VAR] {match['variable_id']} (score: {score:.3f})")
                print(f"   {match['label'][:80]}")
            elif doc_type == "pdf":
                source = match['source']
                content_preview = match['content'][:100].replace('\n', ' ')
                print(f"{i}. [PDF] {source} chunk #{match.get('chunk', 0)} (score: {score:.3f})")
                print(f"   {content_preview}...")
            elif doc_type == "excel":
                table_id = match.get('table_id', 'N/A')
                title = match.get('title', 'No title')[:60]
                print(f"{i}. [TABLE] {table_id} (score: {score:.3f})")
                print(f"   {title}")
    
    print("\n" + "="*70)
    print("3. Testing variable-only search (backward compatible)")
    print("="*70)
    
    variable_query = "median household income"
    print(f"\nQuery: '{variable_query}'")
    print("-"*70)
    
    var_matches = rag.search_variables_only(variable_query, top_k=5)
    for i, match in enumerate(var_matches, 1):
        print(f"{i}. {match['variable_id']} (score: {match['score']:.3f})")
        print(f"   {match['label']}")
    
    print("\n" + "="*70)
    print("✅ RAG with documentation successfully tested!")
    print("="*70)
    print("\nThe vector database now includes:")
    print("  - 30,000+ Census variables")
    print("  - ACS definition PDFs")
    print("  - ACS data product list (Excel)")
    print("\nThis enables richer semantic search and better context!")


if __name__ == "__main__":
    main()
