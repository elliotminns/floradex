from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.auth.utils import get_current_user
from app.users.models import User
from app.identification.model import plant_identifier
from app.config import db
from bson.objectid import ObjectId
from datetime import datetime
import os

router = APIRouter()

@router.post("/", response_model=dict)
async def identify_plant(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Read the image file
        image_bytes = await file.read()
        
        # Generate a unique filename
        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = f"uploads/plants/{filename}"
        
        # Save the image to your storage
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
            
        # Generate URL for the saved image
        image_url = f"/static/uploads/plants/{filename}"
        
        # Identify the plant
        result = plant_identifier.identify(image_bytes)
        
        # Add the image URL to the result
        result["image_url"] = image_url
        
        return result
    except Exception as e:
        print(f"Identification error: {str(e)}")
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
        # Extract data from the request
        plant_type = plant_data.get("plant_type")
        image_url = plant_data.get("image_url")
        
        if not plant_type:
            raise HTTPException(
                status_code=400,
                detail="Plant type is required"
            )
            
        # Create a new plant entry with the image URL
        plant = {
            "type": plant_type,
            "user_id": current_user.id,
            "date_added": datetime.now(),
            "image_url": image_url,
            "confidence": plant_data.get("confidence", 0),
            "all_predictions": plant_data.get("all_predictions", [])
        }
        
        # Insert the plant into the plants collection
        result = db.plants.insert_one(plant)
        plant_id = str(result.inserted_id)
        
        # Update the user's plants list
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$push": {"plants": plant_id}}
        )
        
        return {"success": True, "plant_id": plant_id}
    except Exception as e:
        print(f"Add to collection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add plant to collection: {str(e)}"
        )