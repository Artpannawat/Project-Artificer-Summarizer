from fastapi import FastAPI, HTTPException, Body, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .summarizer.text_processor import TextProcessor
from .summarizer.summarization_model import SummarizationModel
from .models.user import UserSchema, UserLoginSchema, TokenSchema
from .database.mongo import user_collection, create_unique_index, client
from .auth.auth_handler import get_hashed_password, verify_password, sign_jwt, decode_jwt

# Try to import full file processor, fallback to simple one
try:
    from .summarizer.file_processor import FileProcessor
    file_processor = FileProcessor()
    FILE_PROCESSOR_MODE = "full"
except ImportError:
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

@app.on_event("startup")
async def startup_db_client():
    await create_unique_index()

text_processor = TextProcessor()
summarization_model = SummarizationModel()


class TextRequest(BaseModel):
    text: str
    num_sentences: int | None = 5


@app.get("/health")
async def health_check():
    db_ok = True
    try:
        await client.admin.command('ping')
    except Exception:
        db_ok = False
    return {
        "status": "ok", 
        "db": db_ok,
        "file_processor_mode": FILE_PROCESSOR_MODE,
        "supported_file_types": "TXT only" if FILE_PROCESSOR_MODE == "simple" else "PDF, DOC, DOCX, TXT"
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

@app.post("/summarize")
def summarize_text(request: TextRequest):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Input text cannot be empty.")
        
        processed_text = text_processor.clean_text(request.text)
        summary = summarization_model.summarize(processed_text, num_sentences=request.num_sentences or 5)
        
        return {"original_text": request.text, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize-file")
async def summarize_file(
    file: UploadFile = File(...),
    num_sentences: int = Form(5)
):
    try:
        # Validate file
        file_processor.validate_file(file)
        
        # Extract text from file
        extracted_text = await file_processor.extract_text_from_file(file)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="ไม่พบเนื้อหาในไฟล์")
        
        # Process and summarize text
        processed_text = text_processor.clean_text(extracted_text)
        summary = summarization_model.summarize(processed_text, num_sentences=num_sentences)
        
        return {
            "filename": file.filename,
            "file_type": file.content_type,
            "extracted_text_length": len(extracted_text),
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")