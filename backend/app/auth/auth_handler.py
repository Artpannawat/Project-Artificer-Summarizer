import time
import jwt
from typing import Dict
from passlib.context import CryptContext
from decouple import config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

JWT_SECRET = config("JWT_SECRET", default="your-super-secret-key")
# Attempt to get Client ID from env if available, else None (audience check skipped if None)
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default=None)
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import hashlib

def get_hashed_password_v2(password: str) -> str:
    # Pre-hash with SHA256 to bypass bcrypt's 72-byte limit
    # This ensures any length password is safe
    print(f"DEBUG: Hashing password. Original length: {len(password)}")
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    print(f"DEBUG: Pre-hashed length: {len(password_hash)} (Should be 64)")
    return pwd_context.hash(password_hash)

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        # Check for our custom Fallback format (from Vercel robust mode)
        if hashed_password.startswith("SHA256_FALLBACK:"):
            print("DEBUG: Verifying using SHA256 Fallback mode")
            expected_hash = hashed_password.split("SHA256_FALLBACK:")[1]
            # Simple check: Is sha256(password) == suffix?
            current_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return current_hash == expected_hash
            
        # Standard Mode (Bcrypt with SHA256 pre-hashing)
        # Pre-hash input before verifying to match register_v2 logic
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return pwd_context.verify(password_hash, hashed_password)
    except Exception as e:
        print(f"ERROR: Password verification failed: {e}")
        return False

def sign_jwt(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 604800  # Token expires in 7 days
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return {"access_token": token}

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}

import requests

# ... (previous imports)

def verify_google_token(token: str) -> dict | None:
    try:
        # 1. Try treating it as an ID Token (JWT)
        print(f"DEBUG: Verifying as ID Token with Client ID: {GOOGLE_CLIENT_ID}")
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), audience=GOOGLE_CLIENT_ID, clock_skew_in_seconds=10)
        return id_info
    except ValueError:
        # 2. If it's not a valid ID Token, try treating it as an Access Token
        print("DEBUG: ID Token verification failed/invalid. Trying as Access Token...")
        try:
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                user_info = response.json()
                print("DEBUG: Access Token verification successful.")
                return user_info
            else:
                print(f"DEBUG: Access Token verification failed: {response.text}")
                return None
        except Exception as e:
            print(f"DEBUG: Error fetching UserInfo: {e}")
            return None
    except Exception as e:
        print(f"DEBUG: Unexpected error in verify_google_token: {e}")
        return None