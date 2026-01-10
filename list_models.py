import google.generativeai as genai
import os
from pathlib import Path
from decouple import Config, RepositoryEnv

# Load environment variables
env_path = Path(os.getcwd()) / 'backend' / '.env'
config = Config(RepositoryEnv(env_path))
GOOGLE_API_KEY = config("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)

print("Listing available models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
