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
    # 1. Verify file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only .jpg, .png, .webp files are allowed.")
    
    # 2. Get User ID from Token
    payload = decode_jwt(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid Token")

    try:
        from PIL import Image
        import io
        import base64
        
        # 3. Read and Process Image
        # Read file into memory
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Resize if too large (Max 256x256 for avatar) - Keeps DB small
        max_size = (256, 256)
        image.thumbnail(max_size)
        
        # Convert back to bytes (JPEG for compression)
        buffer = io.BytesIO()
        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA'):
            background = Image.new(image.mode[:-1], image.size, (255, 255, 255))
            background.paste(image, image.split()[-1])
            image = background
            
        image.save(buffer, format="JPEG", quality=80)
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # 4. Create Data URI
        avatar_url = f"data:image/jpeg;base64,{img_str}"

        # 5. Update MongoDB
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"avatar_url": avatar_url}}
        )

        return {"avatar_url": avatar_url}
        
    except ImportError:
         raise HTTPException(status_code=500, detail="Server Error: Pillow library missing.")
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Could not process image: {str(e)}")

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
