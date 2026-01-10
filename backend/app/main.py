from fastapi import FastAPI, HTTPException, Body, Depends, UploadFile, File, Form, Request, Header
from fastapi.staticfiles import StaticFiles
import asyncio
from starlette.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .summarizer.text_processor import TextProcessor
from .summarizer.summarization_model import SummarizationModel
from .models.user import UserSchema, UserLoginSchema, TokenSchema
from .database.mongo import user_collection, create_unique_index, client, history_collection
from .auth.auth_handler import get_hashed_password, verify_password, sign_jwt, decode_jwt, verify_google_token
from .routers.users import router as user_router
from .routers.history import router as history_router
from decouple import config
import os
import warnings
# Suppress FutureWarning from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
STARTUP_ERRORS = []

HAS_GENAI = False
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError as e:
    STARTUP_ERRORS.append(f"ImportError: google.generativeai: {e}")
except Exception as e:
    STARTUP_ERRORS.append(f"Error importing google.generativeai: {e}")

from pathlib import Path
from datetime import datetime

# ... (Previous imports and initialization code remains the same up to app definition)

# DEBUG: Print current directory
print(f"DEBUG: Current Directory: {os.getcwd()}")

# Explicitly find .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
# ... (Env loading logic remains same)
if env_path.exists():
    from decouple import Config, RepositoryEnv
    config = Config(RepositoryEnv(env_path))

GOOGLE_API_KEY = config("GOOGLE_API_KEY", default=None)
# ... (Gemini init logic remains same)
if GOOGLE_API_KEY and HAS_GENAI:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = "active" 
    except Exception as e:
        gemini_model = None
        STARTUP_ERRORS.append(f"GenAI Configure Error: {e}")
else:
    gemini_model = None
    if not HAS_GENAI:
        STARTUP_ERRORS.append("GenAI module missing")

import textwrap

# Try to import full file processor, fallback to simple one
try:
    from .summarizer.file_processor import FileProcessor
    file_processor = FileProcessor()
    FILE_PROCESSOR_MODE = "full"
except ImportError as e:
    STARTUP_ERRORS.append(f"FileProcessor Import Error: {e}")
    from .summarizer.simple_file_processor import SimpleFileProcessor
    file_processor = SimpleFileProcessor()
    FILE_PROCESSOR_MODE = "simple"
except Exception as e:
    STARTUP_ERRORS.append(f"FileProcessor Unexpected Error: {e}")
    from .summarizer.simple_file_processor import SimpleFileProcessor
    file_processor = SimpleFileProcessor()
    FILE_PROCESSOR_MODE = "simple"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Include Routers
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(history_router, prefix="/api", tags=["history"]) 

@app.on_event("startup")
async def startup_db_client():
    try:
        await create_unique_index()
        print("DEBUG: Database index created/verified")
    except Exception as e:
        print(f"DEBUG: Startup Database Error: {e}")
        STARTUP_ERRORS.append(f"DB Startup Error: {e}")

    print("DEBUG: Routes registered:")
    for route in app.routes:
        print(f" - {route.path} ({route.name})")

text_processor = TextProcessor()
summarization_model = SummarizationModel()

class TextRequest(BaseModel):
    text: str
    num_sentences: int | None = 5

def summarize_with_ai(text: str, num_sentences: int) -> str:
    if not gemini_model or not HAS_GENAI:
        return f"AI system is offline. Startup Errors: {STARTUP_ERRORS}"
    
    # Strategies: Multi-Model Fallback Priority (Updated based on Diagnostic)
    strategies = [
        {'model': 'gemini-2.5-flash', 'desc': 'Gemini 2.5 Flash (New & Working)'}, 
        {'model': 'gemini-2.0-flash-lite-preview-02-05', 'desc': 'Gemini 2.0 Flash Lite Preview'},
        {'model': 'gemini-2.0-flash', 'desc': 'Gemini 2.0 Flash'},
    ]

    last_error = None
    
    prompt = textwrap.dedent(f"""
        You are a professional summarizer. Please summarize the following text into approximately {num_sentences} sentences.
        
        Requirements:
        - Capture the main points accurately.
        - Maintain the original language of the text (Thai or English).
        - Output ONLY the summary text, no preamble.
        
        Text:
        {text[:20000]}
    """)

    # Try models in order with Smart Retry (Exponential Backoff)
    retry_delay = 1
    
    for i, strategy in enumerate(strategies):
        model_name = strategy['model']
        
        # Exponential Backoff before retrying (if not the first attempt)
        if i > 0:
            print(f"DEBUG: Waiting {retry_delay}s before trying next model...")
            import time
            time.sleep(retry_delay)
            retry_delay *= 2  # 1s, 2s, 4s...
            
        try:
            print(f"DEBUG: Trying {strategy['desc']} (Model: {model_name})...")
            
            # Configure with the single available key
            genai.configure(api_key=GOOGLE_API_KEY)
            
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            if response.text:
                print(f"DEBUG: Success with {model_name}")
                return response.text.strip()
            
        except Exception as e:
            # Log error and continue to next model
            print(f"DEBUG: Failed with {model_name}: {e}")
            last_error = e
            
            # If 429 (Quota), we MUST stop hammering (Backoff is already applied above for next loop)
            # But if it's the LAST model, we stop naturally.
            continue 
    
    # If all failed
    return f"AI Service Error: All models failed. System busy or quota exceeded. Last error: {str(last_error)}"



@app.get("/health")
async def health_check():
    db_status = "ok"
    db_error = None
    try:
        await client.admin.command('ping')
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    # Check what Mongo URI is actually being used (Masked for security)
    from decouple import config
    mongo_uri = config("MONGO_DETAILS", default="NOT_SET")
    masked_uri = "NOT_SET"
    if mongo_uri != "NOT_SET":
         masked_uri = mongo_uri.split("@")[-1] if "@" in mongo_uri else "LOCALHOST_OR_INVALID"
    
    return {
        "status": "ok", 
        "db": db_status,
        "db_error": db_error,
        "startup_errors": STARTUP_ERRORS,
        "mongo_config_source": masked_uri,
        "ai_engine": "active" if gemini_model else "inactive",
    }



@app.post("/register", response_model=TokenSchema, tags=["auth"])
async def register_user(user: UserSchema = Body(...)):
    user_exists = await user_collection.find_one({"email": user.email})
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    hashed_password = get_hashed_password(user.password)
    user.password = hashed_password
    new_user = await user_collection.insert_one(user.dict())
    
    return sign_jwt(str(new_user.inserted_id))

@app.post("/login", response_model=TokenSchema, tags=["auth"])
async def user_login(user: UserLoginSchema = Body(...)):
    user_data = await user_collection.find_one({"email": user.email})
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if verify_password(user.password, user_data["password"]):
        return sign_jwt(str(user_data["_id"]))
    
    raise HTTPException(status_code=401, detail="Invalid email or password.")

@app.options("/auth/google", tags=["auth"])
async def google_login_options():
    return {}

@app.post("/auth/google", tags=["auth"])
async def google_login(token_data: dict = Body(...)):
    try:
        print(f"DEBUG: /auth/google received payload: {token_data}")
        token = token_data.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
            
        # Verify token in threadpool to avoid blocking async event loop
        user_info = await run_in_threadpool(verify_google_token, token)
        if not user_info:
            raise HTTPException(status_code=400, detail="Invalid Google Token (Verification Failed)")
        
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("sub")
        avatar = user_info.get("picture")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in token")

        # Check if user exists
        try:
            user = await user_collection.find_one({"email": email})
        except Exception as db_e:
            raise HTTPException(status_code=500, detail=f"Database Connection Error: {str(db_e)}")
        
        if user:
            # If user exists, return token
            return sign_jwt(str(user["_id"]))
        
        # If user does not exist, create new user
        new_user_data = {
            "username": name,
            "email": email,
            "password": "", # No password for Google users
            "google_id": google_id,
            "avatar_url": avatar
        }
        
        new_user = await user_collection.insert_one(new_user_data)
        return sign_jwt(str(new_user.inserted_id))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Internal Server Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/summarize")
async def summarize_text(
    request: TextRequest, 
    authorization: str | None = Header(default=None)
):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Input text cannot be empty.")
        
        # 1. Basic Summary
        processed_text = text_processor.clean_text(request.text)
        
        # Parallel Execution
        basic_task = run_in_threadpool(summarization_model.summarize, processed_text, num_sentences=request.num_sentences or 5)
        ai_task = run_in_threadpool(summarize_with_ai, request.text, num_sentences=request.num_sentences or 5)
        
        basic_summary, ai_summary = await asyncio.gather(basic_task, ai_task)
        
        result = {
            "original_text": request.text, 
            "basic_summary": basic_summary,
            "ai_summary": ai_summary,
            "comparison_mode": True
        }

        # Auto-save history if user is logged in
        if authorization:
            try:
                # Remove 'Bearer ' prefix if present
                token = authorization.split(" ")[1] if " " in authorization else authorization
                decoded = decode_jwt(token)
                if decoded:
                    user_id = decoded["user_id"]
                    
                    history_item = {
                        "user_id": user_id,
                        "title": request.text[:50] + "..." if len(request.text) > 50 else request.text,
                        "original_text": request.text,
                        "summary_result": result,
                        "created_at": datetime.utcnow(),
                        "is_favorite": False
                    }
                    await history_collection.insert_one(history_item)
                    print(f"DEBUG: History saved for user {user_id}")
            except Exception as e:
                print(f"DEBUG: Failed to save history: {e}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize-file")
async def summarize_file(
    file: UploadFile = File(...),
    num_sentences: int = Form(5),
    authorization: str | None = Header(default=None)
):
    try:
        from starlette.concurrency import run_in_threadpool

        # Validate file
        file_processor.validate_file(file)
        
        # Extract text
        extracted_text = await file_processor.extract_text_from_file(file)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="ไม่พบเนื้อหาในไฟล์")
        
        # Process and summarize text
        processed_text = await run_in_threadpool(text_processor.clean_text, extracted_text)
        
        # Parallel Execution
        basic_task = run_in_threadpool(summarization_model.summarize, processed_text, num_sentences=num_sentences)
        ai_task = run_in_threadpool(summarize_with_ai, extracted_text, num_sentences=num_sentences)
        
        basic_summary, ai_summary = await asyncio.gather(basic_task, ai_task)
        
        result = {
            "filename": file.filename,
            "file_type": file.content_type,
            "extracted_text_length": len(extracted_text),
            "basic_summary": basic_summary,
            "ai_summary": ai_summary,
            "comparison_mode": True
        }

        # Auto-save history if user is logged in
        if authorization:
            try:
                # Remove 'Bearer ' prefix if present
                token = authorization.split(" ")[1] if " " in authorization else authorization
                decoded = decode_jwt(token)
                if decoded:
                    user_id = decoded["user_id"]
                    
                    history_item = {
                        "user_id": user_id,
                        "title": (file.filename + ": " + extracted_text[:30] + "...") if len(extracted_text) > 30 else file.filename,
                        "original_text": extracted_text,
                        "summary_result": result,
                        "created_at": datetime.utcnow(),
                        "is_favorite": False
                    }
                    await history_collection.insert_one(history_item)
                    print(f"DEBUG: File History saved for user {user_id}")
            except Exception as e:
                print(f"DEBUG: Failed to save file history: {e}")

        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")

@app.get("/debug-routes")
def debug_routes():
    return {"routes": [{"path": route.path, "name": route.name} for route in app.routes]}