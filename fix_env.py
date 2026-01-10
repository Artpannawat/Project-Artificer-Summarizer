import os

# Define the path to the .env file in the backend directory
env_path = os.path.join(os.getcwd(), 'backend', '.env')

# Check if the file exists and delete it
if os.path.exists(env_path):
    try:
        os.remove(env_path)
        print(f"Deleted existing .env file at: {env_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

# Content to write (using UTF-8)
# IMPORTANT: Corrected 'GEMINI_API_KEY' to 'GOOGLE_API_KEY' to match backend/app/main.py
env_content = """MONGO_DETAILS=mongodb://localhost:27017
GOOGLE_API_KEY=AIzaSyCdBdbJwy1dcin-ugL0GQKov4AO-SrOQ3o
SECRET_KEY=dev_secret_key
ALGORITHM=HS256
"""

try:
    # Create new .env file with utf-8 encoding
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("Successfully created .env file with UTF-8 encoding.")
    print("-" * 30)
    print(env_content)
    print("-" * 30)
except Exception as e:
    print(f"Error creating file: {e}")
