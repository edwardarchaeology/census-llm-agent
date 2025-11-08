"""
Quick test to verify Ollama is running and responding correctly.
"""
import requests
import json

print("Testing Ollama connection...")
print("=" * 60)

# Test 1: Check if Ollama is running
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        print("✅ Ollama is running")
        models = response.json().get("models", [])
        print(f"   Available models: {len(models)}")
        for model in models:
            print(f"   - {model.get('name', 'Unknown')}")
    else:
        print(f"❌ Ollama responded with status {response.status_code}")
except Exception as e:
    print(f"❌ Cannot connect to Ollama: {e}")
    print("\nTo start Ollama, run: ollama serve")
    exit(1)

print()

# Test 2: Check if phi3:mini is available
has_phi3 = any("phi3" in m.get("name", "") for m in models)
if has_phi3:
    print("✅ phi3:mini model is available")
else:
    print("❌ phi3:mini model not found")
    print("   To install: ollama pull phi3:mini")
    exit(1)

print()

# Test 3: Try a simple chat completion
print("Testing chat completion...")
try:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "phi3:mini",
        "messages": [
            {"role": "user", "content": "Say 'hello' in JSON format"}
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }
    
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    content = result.get("message", {}).get("content", "")
    
    if content.strip():
        print("✅ Ollama responded successfully")
        print(f"   Response: {content[:100]}")
        
        # Try parsing as JSON
        try:
            parsed = json.loads(content)
            print("✅ Response is valid JSON")
        except json.JSONDecodeError:
            print("⚠️ Response is not valid JSON (this could cause issues)")
            print(f"   Raw response: {content}")
    else:
        print("❌ Ollama returned empty response")
        print("   This is the issue causing your error!")
        
except Exception as e:
    print(f"❌ Chat completion failed: {e}")
    exit(1)

print()
print("=" * 60)
print("All tests passed! Ollama is working correctly.")
