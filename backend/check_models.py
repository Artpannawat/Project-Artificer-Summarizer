from google import genai
import os
from pathlib import Path
from decouple import Config, RepositoryEnv

# Robustly find .env file relative to this script
current_dir = Path(__file__).resolve().parent
env_path = current_dir / '.env'

print(f"DEBUG: Looking for .env at: {env_path}")
if not env_path.exists():
    print(f"Error: .env not found at {env_path}")
    exit(1)

config = Config(RepositoryEnv(env_path))
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default=None)

if not GOOGLE_API_KEY:
    print("FATAL: GOOGLE_API_KEY not found in .env")
    exit(1)

print(f"Using API Key: {GOOGLE_API_KEY[:5]}...")

def list_models(version):
    print(f"\n--- Checking API Version: {version} ---")
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY, http_options={'api_version': version})
        found = False
        for model in client.models.list():
            print(f"AVAILABLE: {model.name}")
            found = True
        if not found:
            print("No models found.")
    except Exception as e:
        print(f"ERROR querying {version}: {e}")

list_models('v1beta')
list_models('v1')
