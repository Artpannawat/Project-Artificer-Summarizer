from fastapi import APIRouter, Depends, HTTPException, Body
from ..database.mongo import user_collection
from ..auth.auth_bearer import JWTBearer
from ..auth.auth_handler import decode_jwt, get_password_hash
from bson import ObjectId
from typing import List

router = APIRouter()

# Dependency to check if user is Admin
async def verify_admin(token: str = Depends(JWTBearer())):
    payload = decode_jwt(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid Token")
    
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Admin privileges required")
    
    return user

@router.get("/users", dependencies=[Depends(verify_admin)])
async def get_all_users():
    users = []
    cursor = user_collection.find({})
    async for user in cursor:
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "avatar_url": user.get("avatar_url")
        })
    return users

@router.delete("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def delete_user(user_id: str):
    result = await user_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return {"status": "success", "message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/users/{user_id}/reset-pass", dependencies=[Depends(verify_admin)])
async def reset_user_password(user_id: str):
    # Reset password to default "1234" for simplicity in this version
    hashed_password = get_password_hash("1234")
    result = await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password}}
    )
    if result.modified_count == 1:
        return {"status": "success", "message": "Password reset to '1234'"}
    # If not modified, maybe user not found or password was already 1234
    # Check if user exists to be sure
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
         
    return {"status": "success", "message": "Password reset to '1234'"}

@router.get("/stats", dependencies=[Depends(verify_admin)])
async def get_system_stats():
    user_count = await user_collection.count_documents({})
    # Mocking summary count for now as we don't store summary logs persistently in this DB schema yet
    # In a real app, we would query a History collection.
    # We DO have specific history collections per user, but aggregating them might be slow without a central log.
    # Let's count total users as the primary stat for now.
    
    return {
        "total_users": user_count,
        "active_sessions": 1, # Mock
        "total_summaries": user_count * 5 # Estimate
    }
