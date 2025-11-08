"""
Test a single query end-to-end to verify the app works.
"""
from mvp import run_query, print_result

if __name__ == "__main__":
    print("Testing end-to-end query...\n")
    
    question = "What tract has the highest median income in New Orleans?"
    print(f"Question: {question}\n")
    
    try:
        result = run_query(question)
        print_result(result)
        print("✅ Query completed successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
