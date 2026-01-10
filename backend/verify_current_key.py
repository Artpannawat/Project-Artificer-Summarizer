
import os
import google.generativeai as genai
from decouple import config, RepositoryEnv
from pathlib import Path

# Load .env
env_path = Path(__file__).resolve().parent / '.env'
if env_path.exists():
    from decouple import Config, RepositoryEnv
    config = Config(RepositoryEnv(env_path))
else:
    from decouple import config

api_key = os.environ.get("GOOGLE_API_KEY") or config("GOOGLE_API_KEY", default=None)
print(f"Checking Key: {api_key[:10]}..." if api_key else "No Key Found")

if not api_key:
    exit("No API Key found in .env")

genai.configure(api_key=api_key)

models_to_test = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash-lite-preview-02-05',
    'gemini-2.0-flash',
    'gemini-1.5-flash'
]

print("Starting connectivity test...")

for model_name in models_to_test:
    print(f"\nTesting {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, reply with OK.")
        print(f"SUCCESS: {model_name} responded: {response.text.strip()}")
    except Exception as e:
        print(f"FAILED: {model_name} - {e}")
