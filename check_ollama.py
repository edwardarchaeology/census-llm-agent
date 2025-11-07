"""
Quick check if Ollama is ready to use.
"""
import requests
import sys

OLLAMA_ENDPOINT = "http://localhost:11434"
OLLAMA_MODEL = "phi3:mini"

def check_ollama():
    print("Checking Ollama setup...\n")
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Ollama is running at {OLLAMA_ENDPOINT}")
        
        # Check if model is pulled
        models = [m["name"] for m in data.get("models", [])]
        
        if not models:
            print("\n⚠️  No models found!")
            print(f"   Run: ollama pull {OLLAMA_MODEL}")
            return False
        
        print(f"✓ Found {len(models)} model(s):")
        for model in models:
            marker = " ✓" if OLLAMA_MODEL in model else ""
            print(f"  - {model}{marker}")
        
        if any(OLLAMA_MODEL in m for m in models):
            print(f"\n✅ Ready to use! Run: .venv\\Scripts\\python.exe mvp.py")
            return True
        else:
            print(f"\n⚠️  Model '{OLLAMA_MODEL}' not found")
            print(f"   Run: ollama pull {OLLAMA_MODEL}")
            return False
            
    except requests.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_ENDPOINT}")
        print("\nTo start Ollama:")
        print("1. Open a new PowerShell terminal")
        print("2. Run: ollama serve")
        print("3. Keep it running in the background")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    ready = check_ollama()
    sys.exit(0 if ready else 1)
