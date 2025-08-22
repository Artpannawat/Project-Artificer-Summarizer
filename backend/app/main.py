from fastapi import FastAPI, HTTPException, Body, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import tempfile
from docx import Document
import pdfplumber
from .summarizer.text_processor import TextProcessor
from .summarizer.summarization_model import SummarizationModel
from .models.user import UserSchema, UserLoginSchema, TokenSchema
from .database.mongo import user_collection, create_unique_index, client
from .auth.auth_handler import get_hashed_password, verify_password, sign_jwt, decode_jwt

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


def read_text_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def read_docx_file(file_path: str) -> str:
    try:
        doc = Document(file_path)
        parts: list[str] = []
        for paragraph in doc.paragraphs:
            if paragraph.text and paragraph.text.strip():
                parts.append(paragraph.text)
        # Optionally read tables as well
        for table in getattr(doc, 'tables', []):
            for row in table.rows:
                row_text = [cell.text for cell in row.cells if cell.text and cell.text.strip()]
                if row_text:
                    parts.append(" \t ".join(row_text))
        return "\n".join(parts).strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX file: {str(e)}")


def read_pdf_file(file_path: str) -> str:
    try:
        parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text)
        content = "\n\n".join(parts).strip()
        if not content:
            raise HTTPException(status_code=400, detail="No extractable text found in PDF. The PDF may be scanned images.")
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF file: {str(e)}")


def extract_text_from_file(file: UploadFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        ext = os.path.splitext(file.filename.lower())[1]
        if ext == '.txt':
            text = read_text_file(tmp_path)
        elif ext == '.docx':
            text = read_docx_file(tmp_path)
        elif ext == '.pdf':
            text = read_pdf_file(tmp_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        return text.strip()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/health")
async def health_check():
    db_ok = True
    try:
        await client.admin.command('ping')
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok}

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
async def summarize_file(file: UploadFile = File(...), num_sentences: int = 5):
    try:
        allowed = ['.txt', '.docx', '.pdf']
        ext = os.path.splitext(file.filename.lower())[1]
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types: {', '.join(allowed)}")

        original_text = extract_text_from_file(file)
        if not original_text.strip():
            raise HTTPException(status_code=400, detail="File is empty or contains no readable text.")

        processed_text = text_processor.clean_text(original_text)
        summary = summarization_model.summarize(processed_text, num_sentences=num_sentences or 5)

        return JSONResponse(
            content={
                "original_text": original_text,
                "summary": summary,
                "filename": file.filename,
                "file_size": len(original_text),
                "status": "success"
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")