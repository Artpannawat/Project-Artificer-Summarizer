from fastapi import APIRouter, Depends, HTTPException, Body
from ..database.mongo import db, history_collection
from ..models.history import HistorySchema, HistoryResponseSchema
from ..auth.auth_handler import decode_jwt
from ..auth.auth_bearer import JWTBearer
from typing import List
from bson import ObjectId

router = APIRouter()

# Helper to verify user and get ID
async def get_current_user_id(token: str = Depends(JWTBearer())):
    decoded = decode_jwt(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded["user_id"]

@router.get("/", response_model=List[HistoryResponseSchema])
async def get_history(user_id: str = Depends(get_current_user_id)):
    """Fetch all history items for the current user (Lightweight)"""
    cursor = history_collection.find({"user_id": user_id}).sort("created_at", -1)
    
    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "title": doc["title"],
            "created_at": doc["created_at"],
            "is_favorite": doc.get("is_favorite", False)
        })
    return results

@router.get("/{item_id}")
async def get_history_detail(item_id: str, user_id: str = Depends(get_current_user_id)):
    """Fetch full details of a specific history item"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    item = await history_collection.find_one({"_id": ObjectId(item_id), "user_id": user_id})
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
        
    # Convert ObjectId to str for JSON response
    item["id"] = str(item["_id"])
    del item["_id"]
    return item

@router.delete("/{item_id}")
async def delete_history_item(item_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a specific history item"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await history_collection.delete_one({"_id": ObjectId(item_id), "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"status": "success", "message": "Item deleted"}

@router.delete("/")
async def clear_history(user_id: str = Depends(get_current_user_id)):
    """Delete all history for the user"""
    await history_collection.delete_many({"user_id": user_id})
    return {"status": "success", "message": "All history cleared"}
