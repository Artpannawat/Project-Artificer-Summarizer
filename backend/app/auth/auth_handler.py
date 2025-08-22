import time
import jwt
from typing import Dict
from passlib.context import CryptContext
from decouple import config

JWT_SECRET = config("JWT_SECRET", default="your-super-secret-key")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def sign_jwt(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 600  # Token expires in 10 minutes
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return {"access_token": token}

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}