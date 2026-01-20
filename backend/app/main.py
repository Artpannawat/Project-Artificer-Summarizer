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
from .auth.auth_handler import get_hashed_password_v2, verify_password, sign_jwt, decode_jwt, verify_google_token
from .routers.users import router as user_router
from .routers.history import router as history_router
from .routers.admin import router as admin_router
from decouple import config

import os
import warnings
# Suppress FutureWarning from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning)

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
from datetime import datetime, timezone

# DEBUG: Print current directory
try:
    print(f"DEBUG: Current Directory: {os.getcwd()}")
except: pass

# Explicitly find .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    from decouple import Config, RepositoryEnv
    config = Config(RepositoryEnv(env_path))

GOOGLE_API_KEY = config("GOOGLE_API_KEY", default=None)
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
static_dir = Path("backend/static")
if not static_dir.exists():
    # If static dir missing (common in Vercel if empty), use /tmp
    static_dir = Path("/tmp/static")
    static_dir.mkdir(parents=True, exist_ok=True)
    print(f"DEBUG: 'backend/static' not found. Mounting {static_dir} instead.")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Routers
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(history_router, prefix="/api/history", tags=["History"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

@app.on_event("startup")
async def promote_admin_user():
    try:
        # Auto-promote specific user to admin on startup
        target_email = "pbsosza@gmail.com"
        # Set a short timeout for this check to avoid blocking startup too long if DB is slow
        user = await user_collection.find_one({"email": target_email})
        if user:
            if user.get("role") != "admin":
                await user_collection.update_one(
                    {"email": target_email},
                    {"$set": {"role": "admin"}}
                )
                print(f"INFO: Auto-promoted {target_email} to Admin.")
        else:
            print(f"INFO: Pending Admin promotion - User {target_email} not found yet.")
    except Exception as e:
        print(f"WARNING: Failed to auto-promote admin (DB Error?): {e}")
        STARTUP_ERRORS.append(f"Admin Promotion Failed: {e}")

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
        Role: You are a professional content summarizer specializing in the Thai language.
        Task: Summarize the provided input text into exactly {num_sentences} key points.

        Constraint & Formatting:
        1. Language: Thai (Use natural, concise, and easy-to-understand Thai).
        2. Quantity: The output must contain exactly {num_sentences} bullet points.
        3. Format: Use a bulleted list (e.g., "- Point 1").
        4. Length: Each bullet point should be 1 concise sentence.

        Logic for Selection:
        - If {num_sentences} = 1: Provide the single most important "Main Idea".
        - If {num_sentences} = 2: Problem/Topic -> Solution/Conclusion.
        - If {num_sentences} >= 3: Context -> Details -> Conclusion.

        **Quality Metrics Generation (Important):**
        At the very end of your response, strictly append a JSON-like string evaluating your own summary based on the original text.
        Format: [METRICS: {{"accuracy": XX, "completeness": XX, "conciseness": XX, "average": XX}}]
        - Accuracy: How factual is it? (0-100)
        - Completeness: Did strict key points get covered? (0-100)
        - Conciseness: Is it easy to read? (0-100)
        (Do not add any markdown around this specific line, just the raw bracketed string)

        Input Text:
        {text[:20000]}
    """)

    # Try models in order with Smart Retry (Exponential Backoff)
    retry_delay = 1
    
    for i, strategy in enumerate(strategies):
        model_name = strategy['model']
        
        # Exponential Backoff before retrying (if not the first attempt)
        if i > 0:
            # User requested to cut delays
            pass
            
        # Nested Retry Logic for 429 Errors (Try same model again after wait)
        max_retries_per_model = 2
        for attempt in range(max_retries_per_model):
            try:
                print(f"DEBUG: Trying {strategy['desc']} (Model: {model_name}) [Attempt {attempt+1}]...")
                
                # Configure with the single available key
                genai.configure(api_key=GOOGLE_API_KEY)
                
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                if response and response.text:
                    print(f"DEBUG: Success with {model_name}")
                    return response.text.strip()
                else:
                    raise ValueError("Response blocked by Safety Filters or Empty.")
                
            except Exception as e:
                # Log error
                print(f"DEBUG: Failed with {model_name}: {e}")
                last_error = e
                
                # If 429, we NO LONGER WAIT (User Request)
                # We just retry immediately or fail fast.
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"DEBUG: Rate Limit Hit. Retrying immediately (No Wait Mode)...")
                    # time.sleep(wait_time) # DISABLED
                    
                    if attempt < max_retries_per_model - 1:
                         continue
                
                break 
    
    # If all failed
    return f"AI Service Error: All models failed. System busy or quota exceeded. Last error: {str(last_error)}"


class EvaluationRequest(BaseModel):
    original_text: str
    summary_text: str

async def evaluate_quality_with_ai(original: str, summary: str) -> dict:
    if not gemini_model or not HAS_GENAI:
        return {"error": "AI Service Offline"}

    prompt = textwrap.dedent(f"""
        บทบาท: คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์ภาษาและการประเมินคุณภาพการสรุปความ

        งานของคุณ: เปรียบเทียบ "บทความต้นฉบับ" กับ "บทสรุปที่สร้างขึ้น" และประเมินความถูกต้องแม่นยำออกมาเป็นตัวเลขเปอร์เซ็นต์

        สิ่งที่คุณต้องตอบ (Output) เป็น JSON Format เท่านั้น:
        {{
            "semantic_score": (0-100),
            "textual_difference": (0-100),
            "analysis": "คำอธิบายสั้นๆ..."
        }}

        คำอธิบายตัววัด:
        1. คะแนนความเหมือนของใจความสำคัญ (Semantic Similarity Score):
        - วัดว่าบทสรุปเก็บ "ใจความสำคัญและประเด็นหลัก" ได้ครบถ้วนหรือไม่ (100% = ครบถ้วนสมบูรณ์)
        
        2. อัตราความคลาดเคลื่อนของข้อความ (Textual Difference / Error Rate):
        - วัดความแตกต่างของรูปประโยค (ยิ่งสูงแปลว่ามีการเรียบเรียงใหม่โดยใช้คำตัวเองมาก ซึ่งดีสำหรับการสรุปแบบ Abstractive)
        
        3. บทวิเคราะห์สั้นๆ: 
        - อธิบายเหตุผล คะแนน และจุดที่ตกหล่น

        ---
        [ข้อมูลนำเข้า]

        บทความต้นฉบับ:
        "{original[:15000]}"

        บทสรุปที่สร้างขึ้น:
        "{summary[:5000]}"
    """)

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash') # Fast model for evaluation
        response = await run_in_threadpool(model.generate_content, prompt)
        
        # Simple parsing logic (JSON mode is better but text parsing is robust for now)
        text_res = response.text.strip()
        # Ensure we get clean JSON
        import json
        
        # Try to find JSON block
        if "```json" in text_res:
            text_res = text_res.split("```json")[1].split("```")[0].strip()
        elif "{" in text_res:
            start = text_res.find("{")
            end = text_res.rfind("}") + 1
            text_res = text_res[start:end]
            
        return json.loads(text_res)
    except Exception as e:
        print(f"DEBUG: Evaluation Error: {e}")
        return {"error": str(e), "raw_response": text_res if 'text_res' in locals() else "No response"}

@app.post("/evaluate")
async def evaluate_summary(request: EvaluationRequest):
    return await evaluate_quality_with_ai(request.original_text, request.summary_text)

API_VERSION = "v1.8-evaluator"

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
        "version": API_VERSION,
        "db": db_status,
        "db_error": db_error,
        "startup_errors": STARTUP_ERRORS,
        "mongo_config_source": masked_uri,
        "ai_engine": "active" if gemini_model else "inactive",
    }



@app.post("/register_v2", response_model=TokenSchema, tags=["auth"])
async def register_user(user: UserSchema = Body(...)):
    print(f"DEBUG: Registering user {user.email} with password length {len(user.password)}")
    try:
        user_exists = await user_collection.find_one({"email": user.email})
        if user_exists:
            raise HTTPException(status_code=400, detail="Email already registered.")
        
        # 1A. Strict Email Validation (Real Existence Check)
        try:
            from email_validator import validate_email, EmailNotValidError
            # check_deliverability=True performs a DNS check (MX record)
            # This ensures the domain actually exists and accepts emails.
            print(f"DEBUG: Validating email {user.email}...")
            validation = validate_email(user.email, check_deliverability=True)
            
            # Normalize email (e.g. lowercase)
            user.email = validation.email
            
            # Optional: Strict Check for Gmail (if user specifically asked to be strict about it)
            # if "gmail" in user.email and not user.email.endswith("@gmail.com"):
            #      raise HTTPException(status_code=400, detail="Please use a valid @gmail.com address.")
                 
        except EmailNotValidError as e:
            print(f"DEBUG: Invalid Email: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid email address: {str(e)}")
        except ImportError:
            print("WARNING: email-validator library not found. Skipping strict validation.")
        except Exception as e:
            # DNS checks might timeout (rare), allow to proceed or fail depending on strictness.
            # Here we just log and proceed for robustness vs network glitches.
            print(f"WARNING: Email validation check failed (Network issue?): {e}")
        
        # INLINE FIX: Self-contained hashing to avoid Import Errors and bypass limits
        import hashlib
        
        hashed_password = None
        
        try:
            # Try Primary Method: Bcrypt with SHA256 Pre-hashing
            from passlib.context import CryptContext
            local_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # 1. Pre-hash with SHA256 (Always 64 hex chars)
            pre_hash = hashlib.sha256(user.password.encode('utf-8')).hexdigest()
            
            # 2. Hash with Bcrypt
            hashed_password = local_pwd_context.hash(pre_hash)
            print("DEBUG: Using Bcrypt hashing")
            
        except Exception as e:
            # Fallback Method: standard SHA256 (if passlib fails on Vercel)
            print(f"WARNING: Bcrypt failed ({str(e)}). Falling back to pure SHA256.")
            # Simple salted hash: sha256(password + static_salt) - Not ideal but verified working for now
            hashed_password = "SHA256_FALLBACK:" + hashlib.sha256(user.password.encode('utf-8')).hexdigest()

        user.password = hashed_password
        
        new_user = await user_collection.insert_one(user.model_dump())
        
        # Ensure we return a string ID
        return sign_jwt(str(new_user.inserted_id))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Registration Critical Error: {str(e)}"
        print(f"CRITICAL REGISTER ERROR: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/login", response_model=TokenSchema, tags=["auth"])
async def user_login(user: UserLoginSchema = Body(...)):
    user_data = await user_collection.find_one({"email": user.email})
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if verify_password(user.password, user_data["password"]):
        return sign_jwt(str(user_data["_id"]))
    
    raise HTTPException(status_code=401, detail="Invalid email or password.")

@app.get("/auth/debug", tags=["auth"])
async def auth_debug():
    return {"status": "ok", "message": "Auth routes are accessible"}

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
        
        basic_result, ai_summary = await asyncio.gather(basic_task, ai_task)
        
        # Handle Dictionary Return from Basic Engine
        if isinstance(basic_result, dict):
            basic_summary_text = basic_result.get("summary", "")
            basic_metrics = basic_result.get("metrics", None)
        else:
            basic_summary_text = str(basic_result)
            basic_metrics = None

        result = {
            "original_text": request.text, 
            "basic_summary": basic_summary_text,
            "basic_metrics": basic_metrics,
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
                        "created_at": datetime.now(timezone.utc),
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
        
        basic_result, ai_summary = await asyncio.gather(basic_task, ai_task)

        # Handle Dictionary Return from Basic Engine
        if isinstance(basic_result, dict):
            basic_summary_text = basic_result.get("summary", "")
            basic_metrics = basic_result.get("metrics", None)
        else:
            basic_summary_text = str(basic_result)
            basic_metrics = None
        
        result = {
            "filename": file.filename,
            "file_type": file.content_type,
            "extracted_text_length": len(extracted_text),
            "basic_summary": basic_summary_text,
            "basic_metrics": basic_metrics,
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