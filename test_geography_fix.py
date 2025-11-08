"""
Quick test to verify Geography Agent FIPS code fix
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from agents.geography_agent import GeographyAgent

def test_orleans():
    print("Testing Orleans Parish FIPS resolution...")
    agent = GeographyAgent()
    
    test_queries = [
        "What are the top 5 census tracts in Orleans Parish by median income?",
        "Show me data for New Orleans",
        "Orleans Parish poverty rate"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        parish, fips, confidence = agent.resolve(query)
        print(f"Result: {parish}, FIPS: {fips}, Confidence: {confidence}")
        
        if fips == "071":
            print("✅ Correct FIPS!")
        else:
            print(f"❌ Wrong FIPS! Expected '071', got '{fips}'")

if __name__ == "__main__":
    test_orleans()
