from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..database.mongo import user_collection
from ..auth.auth_bearer import JWTBearer
from ..auth.auth_handler import decode_jwt
import shutil
import os
from pathlib import Path
from bson import ObjectId

router = APIRouter()

# Ensure avatar directory exists
# Ensure avatar directory exists
AVATAR_DIR = Path("backend/static/avatars")
try:
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    # Fallback for Read-Only Filesystems (e.g. Vercel)
    # Note: Files in /tmp are ephemeral and will not persist across restarts.
    # For production, use AWS S3 or Cloudinary.
    AVATAR_DIR = Path("/tmp/avatars")
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload-avatar", dependencies=[Depends(JWTBearer())])
async def upload_avatar(file: UploadFile = File(...), token: str = Depends(JWTBearer())):
    # Verify file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only .jpg and .png files are allowed.")
    
    # Check file size (approximate, reading into memory is risky for large files but OK for <5MB limits)
    # Ideally standard servers handle this, but here we can check if needed.
    # We will proceed with saving.
    
    # Get User ID from Token
    payload = decode_jwt(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid Token")

    # Generate filename
    extension = ".jpg" if file.content_type == "image/jpeg" else ".png"
    filename = f"{user_id}{extension}"
    file_path = AVATAR_DIR / filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # Generate URL (assuming mounted at /static)
    avatar_url = f"/static/avatars/{filename}"

    # Update MongoDB
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"avatar_url": avatar_url}}
    )

    return {"avatar_url": avatar_url}

@router.get("/me", dependencies=[Depends(JWTBearer())])
async def get_current_user_profile(token: str = Depends(JWTBearer())):
    payload = decode_jwt(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid Token")
        
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "username": user["username"],
        "email": user["email"],
        "avatar_url": user.get("avatar_url")
    }
