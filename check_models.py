from google import genai
import os
from pathlib import Path
from decouple import Config, RepositoryEnv

# Load environment variables
env_path = Path(os.getcwd()) / 'backend' / '.env'
if not env_path.exists():
    print(f"Error: .env not found at {env_path}")
    exit(1)

config = Config(RepositoryEnv(env_path))
GOOGLE_API_KEY = config("GOOGLE_API_KEY")

print(f"Using API Key: {GOOGLE_API_KEY[:5]}...")

try:
    print("-" * 30)
    print("Checking v1beta...")
    client_beta = genai.Client(api_key=GOOGLE_API_KEY, http_options={'api_version': 'v1beta'})
    for model in client_beta.models.list():
        if 'generateContent' in model.supported_generation_methods:
            print(f"v1beta Model: {model.name}")
            
    print("-" * 30)
    print("Checking v1...")
    client_v1 = genai.Client(api_key=GOOGLE_API_KEY, http_options={'api_version': 'v1'})
    for model in client_v1.models.list():
        if 'generateContent' in model.supported_generation_methods:
            print(f"v1 Model: {model.name}")

except Exception as e:
    print(f"Error fetching models: {e}")
    import traceback
    traceback.print_exc()
