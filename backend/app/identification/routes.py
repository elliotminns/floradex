from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.auth.utils import get_current_user
from app.users.models import User
from app.identification.model import plant_identifier
from app.config import db
from bson.objectid import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=dict)
async def identify_plant(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Read the image file
        image_bytes = await file.read()
        
        # Identify the plant
        result = plant_identifier.identify(image_bytes)
        
        return {
            "success": True,
            "identification": result
        }
    except Exception as e:
        print(f"Identification error: {str(e)}")  # Log the full error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to identify plant: {str(e)}"
        )

@router.post("/add-to-collection", response_model=dict)
async def add_to_collection(
    plant_data: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        # Extract plant type from the data sent by the frontend
        # This should match the key that your frontend sends
        plant_type = plant_data.get("plant_type")
        
        if not plant_type:
            raise HTTPException(
                status_code=400,
                detail="Plant type is required"
            )
        
        # Create a new plant entry
        plant = {
            "type": plant_type,
            "user_id": current_user.id,
            "date_added": datetime.now(),
            "image_url": plant_data.get("image_url", ""),
            "nickname": plant_data.get("nickname", "")
        }
        
        # Insert the plant into the plants collection
        result = db.plants.insert_one(plant)
        plant_id = str(result.inserted_id)
        
        # Add the plant ID to the user's plants list
        # Wrap the user ID in ObjectId()
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$push": {"plants": plant_id}}
        )
        
        return {"success": True, "plant_id": plant_id}
    except Exception as e:
        print(f"Add to collection error: {str(e)}")  # Log the full error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add plant to collection: {str(e)}"
        )