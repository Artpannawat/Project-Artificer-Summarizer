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
import requests
import json
import base64
import time

STARTUP_ERRORS = []

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

# --- Lightweight Gemini Client (REST API) ---
def call_gemini_api(model_name: str, prompt: str, file_data: dict = None) -> str:
    """
    Calls Gemini API via REST (requests) to avoid heavy google-generativeai dependency.
    file_data: {'mime_type': str, 'data': bytes}
    """
    if not GOOGLE_API_KEY:
        raise Exception("GOOGLE_API_KEY not found.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    parts = [{"text": prompt}]
    
    if file_data:
        # Add inline data (Base64)
        b64_data = base64.b64encode(file_data['data']).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": file_data['mime_type'],
                "data": b64_data
            }
        })
    
    payload = {
        "contents": [{
            "parts": parts
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        error_detail = response.text
        if response.status_code == 429:
             raise Exception(f"429 Quota Exceeded: {error_detail}")
        raise Exception(f"Gemini API Error {response.status_code}: {error_detail}")
        
    result = response.json()
    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        # Fallback for safety blocked responses
        if 'promptFeedback' in result:
             raise Exception(f"Blocked by safety settings: {result['promptFeedback']}")
        raise Exception(f"Invalid API response structure: {str(result)}")


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

    # กลยุทธ์: ลำดับความสำคัญการ Fallback หลายโมเดล (ขึ้นอยู่กับความพร้อมใช้งานจริง)
    strategies = [
        {'model': 'gemini-2.0-flash', 'desc': 'Gemini 2.0 Flash (Standard)'},
        {'model': 'gemini-2.0-flash-lite', 'desc': 'Gemini 2.0 Flash Lite (Efficient)'}, # Note: Verify exact model name supported by API
        {'model': 'gemini-2.0-flash-exp', 'desc': 'Gemini 2.0 Flash Exp'},
        {'model': 'gemini-1.5-flash', 'desc': 'Gemini 1.5 Flash (Fallback)'},
        {'model': 'gemini-pro', 'desc': 'Gemini Pro (Legacy)'},
    ]

    last_error = None
    
    prompt = textwrap.dedent(f"""
        Role: You are an expert Document Analyst and Content Summarizer using Thai language.
        Task: Analyze the raw text extracted from a PDF/DOCX document, clean the noise, and provide a high-quality summary.

        Input Context:
        The input text may contain "extraction artifacts" such as:
        - Script/Storyboard metadata (e.g., "Scene:", "Voice Over:", "Cut to:", "Camera Angle").
        - Broken sentences or weird line breaks (typical from PDF extraction).
        - Headers, footers, or page numbers.

        Instructions:
        1. **Filter Noise:** Ignore technical instructions, stage directions, scene numbers, or list of actors UNLESS they are crucial to understanding the story/context.
        2. **Reconstruct:** Mentally join broken lines or split sentences to form coherent thoughts before summarizing.
        3. **Summarize:** Extract the *core message* and *intent* of the document.
            - If it's a story/script: Summarize the plot and key message.
            - If it's an academic/formal doc: Summarize the key findings.
        4. **Format:** Output exactly {num_sentences} bullet points in Thai.

        Output Requirement:
        - Language: Natural, professional Thai.
        - Style: Concise, clear, and easy to read.
        - Do NOT output the raw cleaned text, only the final summary.

        **Quality Metrics Generation (Important):**
        At the very end of your response, strictly append a JSON-like string evaluating your own summary based on the original text.
        Format: [METRICS: {{"accuracy": XX, "completeness": XX, "conciseness": XX, "average": XX}}]
        - Accuracy: How factual is it? (0-100)
        - Completeness: Did strict key points get covered? (0-100)
        - Conciseness: Is it easy to read? (0-100)
        (Do not add any markdown around this specific line, just the raw bracketed string)

        Raw Input Text:
        "{text}"
    """)

    # Try models in order with Smart Retry
    retry_delay = 1
    all_errors = []

    for i, strategy in enumerate(strategies):
        model_name = strategy['model']
        
        # Exponential Backoff ก่อนลองโมเดลถัดไป
        if i > 0:
            print(f"DEBUG: Waiting {retry_delay}s before trying next model...")
            time.sleep(retry_delay)
            retry_delay *= 2 
            
        # ตรรกะการลองซ้ำแบบซ้อน (Nested Retry) สำหรับข้อผิดพลาด 429
        max_retries_per_model = 3
        for attempt in range(max_retries_per_model):
            try:
                print(f"DEBUG: Trying {strategy['desc']} (Model: {model_name}) [Attempt {attempt+1}]...")
                
                # Use standard requests REST API
                response_text = call_gemini_api(model_name, prompt)
                
                if response_text:
                    print(f"DEBUG: Success with {model_name}")
                    return response_text.strip()
                else:
                    raise ValueError("Empty response text.")
                
            except Exception as e:
                print(f"DEBUG: Failed with {model_name}: {e}")
                error_str = str(e)
                
                # กู้คืน: การรอคอยอัจฉริยะ (Smart Wait) สำหรับ 429 (สำคัญสำหรับคีย์ฟรี)
                if "429" in error_str or "quota" in error_str.lower():
                    print(f"DEBUG: Rate Limit Hit. Retrying...")
                    time.sleep(2) # Short wait
                    if attempt < max_retries_per_model - 1:
                         continue
                
                # ถ้าเป็น 404 (ไม่พบ model) ให้ break ไป model ถัดไปทันที
                if "404" in error_str or "not found" in error_str.lower():
                     all_errors.append(f"{model_name}: Model Not Found")
                     break
                
                all_errors.append(f"{model_name}: {error_str}")
                break
        
    # ถ้าล้มเหลวทั้งหมด
    return f"AI Service Error: All models failed. Details: {'; '.join(all_errors)}"


class EvaluationRequest(BaseModel):
    original_text: str
    summary_text: str

async def evaluate_quality_with_ai(original: str, summary: str) -> dict:
    if not GOOGLE_API_KEY:
        return {"error": "AI Service Offline (No Key)"}

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
        # ใช้ run_in_threadpool สำหรับ blocking I/O (requests)
        response_text = await run_in_threadpool(call_gemini_api, 'gemini-2.0-flash', prompt)
        
        # ตรรกะการแยกวิเคราะห์ง่ายๆ (โหมด JSON ดีกว่า แต่การแยกวิเคราะห์ข้อความก็แข็งแกร่งพอสำหรับตอนนี้)
        text_res = response_text.strip()
        
        # พยายามหาบล็อก JSON
        if "```json" in text_res:
            text_res = text_res.split("```json")[1].split("```")[0].strip()
        elif "{" in text_res:
            start = text_res.find("{")
            end = text_res.rfind("}") + 1
            text_res = text_res[start:end]
            
        return json.loads(text_res)
    except Exception as e:
        print(f"DEBUG: Evaluation Error: {e}")
        return {"error": str(e)}

@app.post("/evaluate")
async def evaluate_summary(request: EvaluationRequest):
    return await evaluate_quality_with_ai(request.original_text, request.summary_text)

API_VERSION = "v1.8-lite-deploy"

@app.get("/health")
async def health_check():
    db_status = "ok"
    db_error = None
    try:
        await client.admin.command('ping')
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    return {
        "status": "ok", 
        "version": API_VERSION,
        "db": db_status,
        "db_error": db_error,
        "startup_errors": STARTUP_ERRORS,
        "ai_engine": "active (REST)" if GOOGLE_API_KEY else "inactive",
    }



@app.post("/register_v2", response_model=TokenSchema, tags=["auth"])
async def register_user(user: UserSchema = Body(...)):
    print(f"DEBUG: Registering user {user.email} with password length {len(user.password)}")
    try:
        user_exists = await user_collection.find_one({"email": user.email})
        if user_exists:
            raise HTTPException(status_code=400, detail="Email already registered.")
        
        # 1A. การตรวจสอบอีเมลอย่างเข้มงวด (ตรวจสอบการมีอยู่จริง)
        try:
            from email_validator import validate_email, EmailNotValidError
            # check_deliverability=True performs a DNS check (MX record) --> check_deliverability=True ทำการตรวจสอบ DNS (ระเบียน MX)
            # สิ่งนี้ทำให้แน่ใจว่าโดเมนมีอยู่จริงและรับอีเมล
            print(f"DEBUG: Validating email {user.email}...")
            validation = validate_email(user.email, check_deliverability=True)
            
            # ทำให้อีเมลเป็นมาตรฐาน (เช่น ตัวพิมพ์เล็ก)
            user.email = validation.email
                 
        except EmailNotValidError as e:
            print(f"DEBUG: Invalid Email: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid email address: {str(e)}")
        except ImportError:
            print("WARNING: email-validator library not found. Skipping strict validation.")
        except Exception as e:
            # การตรวจสอบ DNS อาจหมดเวลา (หายาก) อนุญาตให้ดำเนินการต่อหรือล้มเหลวขึ้นอยู่กับความเข้มงวด
            # ที่นี่เราแค่บันทึกและดำเนินการต่อเพื่อความทนทานต่อปัญหาเครือข่าย
            print(f"WARNING: Email validation check failed (Network issue?): {e}")
        
        # การแก้ไขแบบแทรกในบรรทัด: การแฮชแบบในตัวเพื่อหลีกเลี่ยงข้อผิดพลาด Import และข้ามข้อจำกัด
        import hashlib
        
        hashed_password = None
        
        try:
            # ลองวิธีหลัก: Bcrypt พร้อม Pre-hashing SHA256
            from passlib.context import CryptContext
            local_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # 1. Pre-hash ด้วย SHA256 (64 ตัวอักษรฐานสิบหกเสมอ)
            pre_hash = hashlib.sha256(user.password.encode('utf-8')).hexdigest()
            
            # 2. แฮชด้วย Bcrypt
            hashed_password = local_pwd_context.hash(pre_hash)
            print("DEBUG: Using Bcrypt hashing")
            
        except Exception as e:
            # วิธีสำรอง: SHA256 มาตรฐาน (ถ้า passlib ล้มเหลวบน Vercel)
            print(f"WARNING: Bcrypt failed ({str(e)}). Falling back to pure SHA256.")
            # แฮชแบบใส่เกลืออย่างง่าย: sha256(password + static_salt) - ไม่ดีที่สุดแต่ตรวจสอบแล้วว่าใช้งานได้
            hashed_password = "SHA256_FALLBACK:" + hashlib.sha256(user.password.encode('utf-8')).hexdigest()

        user.password = hashed_password
        
        new_user = await user_collection.insert_one(user.model_dump())
        
        # ตรวจสอบให้แน่ใจว่าเราคืนค่า ID เป็นสตริง
        return sign_jwt(str(new_user.inserted_id))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Register Error: {str(e)}"
        print(f"CRITICAL REGISTER ERROR: {error_msg}")
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
        error_msg = f"Internal Server Error: {str(e)}"
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
        
        # 1. การสรุปแบบพื้นฐาน
        processed_text = text_processor.clean_text(request.text)
        
        # การประมวลผลแบบขนาน
        basic_task = run_in_threadpool(summarization_model.summarize, processed_text, num_sentences=request.num_sentences or 5)
        ai_task = run_in_threadpool(summarize_with_ai, request.text, num_sentences=request.num_sentences or 5)
        
        basic_result, ai_summary = await asyncio.gather(basic_task, ai_task)
        
        # จัดการการคืนค่าแบบ Dictionary จาก Basic Engine
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
        
        # --- AI OCR Fallback (Hybrid Mode) ---
        if not extracted_text:
            print("DEBUG: Local text extraction returned empty. Attempting AI OCR...")
            
            # Reset cursor to read bytes for OCR
            await file.seek(0)
            file_bytes = await file.read()
            
            try:
                extracted_text = await perform_ocr_with_gemini(file_bytes, file.content_type)
            except Exception as e:
                print(f"DEBUG: OCR Fallback failed: {e}")
                raise HTTPException(status_code=400, detail=f"ไม่สามารถอ่านไฟล์ได้ (Scanned PDF) และ AI OCR ล้มเหลว: {str(e)}")
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="ไม่พบเนื้อหาในไฟล์ (Blank File)")
        
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

        # Auto-save history if user is logged in --> บันทึกประวัติอัตโนมัติถ้าผู้ใช้เข้าสู่ระบบแล้ว
        if authorization:
            try:
                # Remove 'Bearer ' prefix if present --> ลบคำนำหน้า 'Bearer ' ถ้ามี
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

async def perform_ocr_with_gemini(file_bytes: bytes, mime_type: str) -> str:
    """Fallback OCR using Gemini REST API"""
    if not GOOGLE_API_KEY:
        raise Exception("AI System (Gemini) is explicitly required for scanned documents (OCR).")

    # Priority list of models to try for OCR
    ocr_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite-preview-02-05", 
        "gemini-1.5-flash",
    ]
    
    last_error = None
    prompt = "Transcribe the text from this image/document exactly as it appears. Output ONLY the text content. Do not add any markdown formatting or comments."
    
    # Prepare inline data (Request library needs bytes, but our wrapper handles it)
    file_data = {'mime_type': mime_type, 'data': file_bytes}
    
    for model_name in ocr_models:
        try:
            print(f"DEBUG: Attempting AI OCR with model: {model_name}")
            
            # Simple retry for 429
            for attempt in range(2):
                try:
                    # Use run_in_threadpool for blocking request
                    response_text = await run_in_threadpool(call_gemini_api, model_name, prompt, file_data)
                    return response_text.strip()
                except Exception as e:
                    if "429" in str(e):
                        print(f"DEBUG: 429 Quota Exceeded for {model_name}. Retrying...")
                        time.sleep(2)
                        continue
                    else:
                        raise e 
            
        except Exception as e:
            print(f"DEBUG: Failed with {model_name}: {e}")
            last_error = e
            continue
            
    raise Exception(f"All OCR models failed. Last error: {str(last_error)}")

@app.get("/debug-routes")
def debug_routes():
    return {"routes": [{"path": route.path, "name": route.name} for route in app.routes]}
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


    # กลยุทธ์: ลำดับความสำคัญการ Fallback หลายโมเดล (ขึ้นอยู่กับความพร้อมใช้งานจริง)
    strategies = [
        {'model': 'gemini-2.0-flash', 'desc': 'Gemini 2.0 Flash (Standard)'},
        {'model': 'gemini-2.0-flash-lite', 'desc': 'Gemini 2.0 Flash Lite (Efficient)'},
        {'model': 'gemini-2.5-flash', 'desc': 'Gemini 2.5 Flash (Newest)'},
        {'model': 'gemini-1.5-flash-latest', 'desc': 'Gemini 1.5 Flash Latest (Fallback)'},
    ]

    last_error = None
    
    prompt = textwrap.dedent(f"""
        Role: You are an expert Document Analyst and Content Summarizer using Thai language.
        Task: Analyze the raw text extracted from a PDF/DOCX document, clean the noise, and provide a high-quality summary.

        Input Context:
        The input text may contain "extraction artifacts" such as:
        - Script/Storyboard metadata (e.g., "Scene:", "Voice Over:", "Cut to:", "Camera Angle").
        - Broken sentences or weird line breaks (typical from PDF extraction).
        - Headers, footers, or page numbers.

        Instructions:
        1. **Filter Noise:** Ignore technical instructions, stage directions, scene numbers, or list of actors UNLESS they are crucial to understanding the story/context.
        2. **Reconstruct:** Mentally join broken lines or split sentences to form coherent thoughts before summarizing.
        3. **Summarize:** Extract the *core message* and *intent* of the document.
            - If it's a story/script: Summarize the plot and key message.
            - If it's an academic/formal doc: Summarize the key findings.
        4. **Format:** Output exactly {num_sentences} bullet points in Thai.

        Output Requirement:
        - Language: Natural, professional Thai.
        - Style: Concise, clear, and easy to read.
        - Do NOT output the raw cleaned text, only the final summary.

        **Quality Metrics Generation (Important):**
        At the very end of your response, strictly append a JSON-like string evaluating your own summary based on the original text.
        Format: [METRICS: {{"accuracy": XX, "completeness": XX, "conciseness": XX, "average": XX}}]
        - Accuracy: How factual is it? (0-100)
        - Completeness: Did strict key points get covered? (0-100)
        - Conciseness: Is it easy to read? (0-100)
        (Do not add any markdown around this specific line, just the raw bracketed string)

        Raw Input Text:
        "{text}"
    """)

    # Try models in order with Smart Retry
    retry_delay = 1
    
    # ลองใช้โมเดลตามลำดับด้วย Smart Retry (Exponential Backoff)
    retry_delay = 1
    all_errors = []

    for i, strategy in enumerate(strategies):
        model_name = strategy['model']
        
        # Exponential Backoff ก่อนลองโมเดลถัดไป
        if i > 0:
            print(f"DEBUG: Waiting {retry_delay}s before trying next model...")
            import time
            time.sleep(retry_delay)
            retry_delay *= 2 
            
        # ตรรกะการลองซ้ำแบบซ้อน (Nested Retry) สำหรับข้อผิดพลาด 429
        max_retries_per_model = 5
        for attempt in range(max_retries_per_model):
            try:
                print(f"DEBUG: Trying {strategy['desc']} (Model: {model_name}) [Attempt {attempt+1}]...")
                
                genai.configure(api_key=GOOGLE_API_KEY)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                if response and response.text:
                    print(f"DEBUG: Success with {model_name}")
                    return response.text.strip()
                else:
                    raise ValueError("Response blocked by Safety Filters or Empty.")
                
            except Exception as e:
                print(f"DEBUG: Failed with {model_name}: {e}")
                
                # กู้คืน: การรอคอยอัจฉริยะ (Smart Wait) สำหรับ 429 (สำคัญสำหรับคีย์ฟรี)
                if "429" in str(e) or "quota" in str(e).lower():
                    # คำขอจากผู้ใช้: คีย์ใหม่ = ไม่ต้องรอ!
                    print(f"DEBUG: Rate Limit Hit. Retrying immediately (No Wait Mode)...")
                    # import time
                    # ... wait logic disabled ...
                    # time.sleep(wait_time)
                    
                    if attempt < max_retries_per_model - 1:
                         continue
                
                # ถ้าเป็น 404/400 (ไม่พบ / อาร์กิวเมนต์ไม่ถูกต้อง) หรือ Limit 0 ให้ล้มเหลวทันทีเพื่อไปโมเดลถัดไป
                if "404" in str(e) or "not found" in str(e).lower() or "limit: 0" in str(e).lower():
                     all_errors.append(f"{model_name}: {str(e)}") # Show FULL error
                     break
                
                all_errors.append(f"{model_name}: {str(e)}")
                break
        
        # Exponential Backoff สำหรับโมเดลถัดไป
        if i < len(strategies) - 1:
             retry_delay *= 2 
    
    # ถ้าล้มเหลวทั้งหมด
    return f"AI Service Error: All models failed. Details: {'; '.join(all_errors)}"


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
        model = genai.GenerativeModel('gemini-2.0-flash') # โมเดลที่รวดเร็วสำหรับการประเมินผล
        response = await run_in_threadpool(model.generate_content, prompt)
        
        # ตรรกะการแยกวิเคราะห์ง่ายๆ (โหมด JSON ดีกว่า แต่การแยกวิเคราะห์ข้อความก็แข็งแกร่งพอสำหรับตอนนี้)
        text_res = response.text.strip()
        # ตรวจสอบให้แน่ใจว่าได้ JSON ที่สะอาด
        import json
        
        # พยายามหาบล็อก JSON
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
        
        # 1A. การตรวจสอบอีเมลอย่างเข้มงวด (ตรวจสอบการมีอยู่จริง)
        try:
            from email_validator import validate_email, EmailNotValidError
            # check_deliverability=True performs a DNS check (MX record) --> check_deliverability=True ทำการตรวจสอบ DNS (ระเบียน MX)
            # สิ่งนี้ทำให้แน่ใจว่าโดเมนมีอยู่จริงและรับอีเมล
            print(f"DEBUG: Validating email {user.email}...")
            validation = validate_email(user.email, check_deliverability=True)
            
            # ทำให้อีเมลเป็นมาตรฐาน (เช่น ตัวพิมพ์เล็ก)
            user.email = validation.email
            
            # ทางเลือก: ตรวจสอบอย่างเข้มงวดสำหรับ Gmail (ถ้าผู้ใช้ขอให้เข้มงวดเรื่องนี้)
            # if "gmail" in user.email and not user.email.endswith("@gmail.com"):
            #      raise HTTPException(status_code=400, detail="Please use a valid @gmail.com address.")
                 
        except EmailNotValidError as e:
            print(f"DEBUG: Invalid Email: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid email address: {str(e)}")
        except ImportError:
            print("WARNING: email-validator library not found. Skipping strict validation.")
        except Exception as e:
            # การตรวจสอบ DNS อาจหมดเวลา (หายาก) อนุญาตให้ดำเนินการต่อหรือล้มเหลวขึ้นอยู่กับความเข้มงวด
            # ที่นี่เราแค่บันทึกและดำเนินการต่อเพื่อความทนทานต่อปัญหาเครือข่าย
            print(f"WARNING: Email validation check failed (Network issue?): {e}")
        
        # การแก้ไขแบบแทรกในบรรทัด: การแฮชแบบในตัวเพื่อหลีกเลี่ยงข้อผิดพลาด Import และข้ามข้อจำกัด
        import hashlib
        
        hashed_password = None
        
        try:
            # ลองวิธีหลัก: Bcrypt พร้อม Pre-hashing SHA256
            from passlib.context import CryptContext
            local_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # 1. Pre-hash ด้วย SHA256 (64 ตัวอักษรฐานสิบหกเสมอ)
            pre_hash = hashlib.sha256(user.password.encode('utf-8')).hexdigest()
            
            # 2. แฮชด้วย Bcrypt
            hashed_password = local_pwd_context.hash(pre_hash)
            print("DEBUG: Using Bcrypt hashing")
            
        except Exception as e:
            # วิธีสำรอง: SHA256 มาตรฐาน (ถ้า passlib ล้มเหลวบน Vercel)
            print(f"WARNING: Bcrypt failed ({str(e)}). Falling back to pure SHA256.")
            # แฮชแบบใส่เกลืออย่างง่าย: sha256(password + static_salt) - ไม่ดีที่สุดแต่ตรวจสอบแล้วว่าใช้งานได้
            hashed_password = "SHA256_FALLBACK:" + hashlib.sha256(user.password.encode('utf-8')).hexdigest()

        user.password = hashed_password
        
        new_user = await user_collection.insert_one(user.model_dump())
        
        # ตรวจสอบให้แน่ใจว่าเราคืนค่า ID เป็นสตริง
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
        
        # 1. การสรุปแบบพื้นฐาน
        processed_text = text_processor.clean_text(request.text)
        
        # การประมวลผลแบบขนาน
        basic_task = run_in_threadpool(summarization_model.summarize, processed_text, num_sentences=request.num_sentences or 5)
        ai_task = run_in_threadpool(summarize_with_ai, request.text, num_sentences=request.num_sentences or 5)
        
        basic_result, ai_summary = await asyncio.gather(basic_task, ai_task)
        
        # จัดการการคืนค่าแบบ Dictionary จาก Basic Engine
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
        
        # --- AI OCR Fallback (Hybrid Mode) ---
        if not extracted_text:
            print("DEBUG: Local text extraction returned empty. Attempting AI OCR...")
            
            # Check if file is suitable for OCR (PDF or Image)
            # file_processor guarantees PDF or Image types generally, but let's double check content type handled by Gemini
            # Supported: application/pdf, image/jpeg, image/png, etc.
            
            # Reset cursor to read bytes for OCR
            await file.seek(0)
            file_bytes = await file.read()
            
            try:
                extracted_text = await perform_ocr_with_gemini(file_bytes, file.content_type)
            except Exception as e:
                print(f"DEBUG: OCR Fallback failed: {e}")
                raise HTTPException(status_code=400, detail=f"ไม่สามารถอ่านไฟล์ได้ (Scanned PDF) และ AI OCR ล้มเหลว: {str(e)}")
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="ไม่พบเนื้อหาในไฟล์ (Blank File)")
        
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

        # Auto-save history if user is logged in --> บันทึกประวัติอัตโนมัติถ้าผู้ใช้เข้าสู่ระบบแล้ว
        if authorization:
            try:
                # Remove 'Bearer ' prefix if present --> ลบคำนำหน้า 'Bearer ' ถ้ามี
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

async def perform_ocr_with_gemini(file_bytes: bytes, mime_type: str) -> str:
    """Fallback OCR using Gemini with multiple model fallbacks and retry logic"""
    if not HAS_GENAI or not GOOGLE_API_KEY:
        raise Exception("AI System (Gemini) is explicitly required for scanned documents (OCR).")

    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Priority list of models to try for OCR
    ocr_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite-preview-02-05", # Try the lite version
        "gemini-2.0-flash-exp",
        "gemini-flash-latest" # Fallback to latest stable flash alias
    ]
    
    last_error = None
    
    print("DEBUG: Triggering AI OCR with fallback strategy...")
    
    prompt = "Transcribe the text from this image/document exactly as it appears. Output ONLY the text content. Do not add any markdown formatting or comments."
    
    for model_name in ocr_models:
        try:
            print(f"DEBUG: Attempting AI OCR with model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Simple retry for 429 within the model attempt
            for attempt in range(2):
                try:
                    response = await run_in_threadpool(
                        model.generate_content,
                        contents=[
                            {'mime_type': mime_type, 'data': file_bytes},
                            prompt
                        ]
                    )
                    
                    if response and response.text:
                        print(f"DEBUG: AI OCR Success with {model_name}")
                        return response.text.strip()
                except Exception as e:
                    if "429" in str(e):
                        print(f"DEBUG: 429 Quota Exceeded for {model_name}. Retrying...")
                        import time
                        time.sleep(2) # Short wait before internal retry
                        continue
                    else:
                        raise e # Re-raise other errors to break internal loop and try next model
            
        except Exception as e:
            print(f"DEBUG: Failed with {model_name}: {e}")
            last_error = e
            continue
            
    # If we get here, all models failed
    error_msg = f"All OCR models failed. Last error: {str(last_error)}"
    print(f"DEBUG: {error_msg}")
    raise Exception(error_msg)

@app.get("/debug-routes")
def debug_routes():
    return {"routes": [{"path": route.path, "name": route.name} for route in app.routes]}