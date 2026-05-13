from google import genai
import os

# Use hardcoded API key for testing (or get from env)
api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyCtaMFOgg40_1yIycqwuiCkrXCDqYM-pOc"

print(f"🔑 API Key present: {bool(api_key)}")
print(f"🔑 API Key length: {len(api_key) if api_key else 0}\n")

try:
    client = genai.Client(api_key=api_key)
    print("📋 Available Gemini Models:\n")
    for m in client.models.list():
        print(f"  • {m.name}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
