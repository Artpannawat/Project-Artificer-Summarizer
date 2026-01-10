import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

log("Starting import checks...")

try:
    log("Importing fastapi...")
    from fastapi import FastAPI
    log("Importing pythainlp...")
    from pythainlp import sent_tokenize
    log("Importing sklearn...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    log("Importing networkx...")
    import networkx
    log("Importing google.generativeai...")
    import google.generativeai
    log("Importing motor...")
    from motor.motor_asyncio import AsyncIOMotorClient
    log("Importing passlib...")
    from passlib.context import CryptContext
    log("Importing app.database.mongo...")
    from app.database import mongo
    log("Imports finished successfully.")

except Exception as e:
    log(f"CRASH: {e}")
except KeyboardInterrupt:
    log("HANG DETECTED: Interrupted.")
