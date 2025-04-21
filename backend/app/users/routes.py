from fastapi import APIRouter, Depends, HTTPException
from bson.objectid import ObjectId

from app.config import db
from app.auth.utils import get_current_user, get_password_hash
from app.users.models import User, UserUpdate

router = APIRouter()

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=User)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    # Prepare update data
    update_data = {}
    
    if user_update.username:
        # Check if username is taken
        if user_update.username != current_user.username:
            existing_user = db.users.find_one({"username": user_update.username})
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username already taken"
                )
        update_data["username"] = user_update.username
    
    if user_update.password:
        update_data["hashed_password"] = get_password_hash(user_update.password)
    
    # Update the user if there are changes
    if update_data:
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": update_data}
        )
    
    # Get the updated user
    updated_user = db.users.find_one({"_id": ObjectId(current_user.id)})
    return updated_user

@router.delete("/me", response_model=dict)
async def delete_user(current_user: User = Depends(get_current_user)):
    # Print debugging information
    print(f"Deleting user: {current_user.username} with ID: {current_user.id}")
    
    try:
        # Delete all plants associated with the user
        plants_result = db.userplants.delete_many({
            "$or": [
                {"user_id": str(current_user.id)},
                {"user_id": current_user.id}  # Without string conversion
            ]
        })
        print(f"Deleted {plants_result.deleted_count} plants")
        
        # Delete the user
        user_result = db.users.delete_one({"_id": ObjectId(current_user.id)})
        print(f"User deletion result: {user_result.deleted_count}")
        
        if user_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "message": "Account deleted successfully"}
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")