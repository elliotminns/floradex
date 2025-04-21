from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from bson.objectid import ObjectId
import os
import base64
from datetime import datetime

from app.config import db
from app.auth.utils import get_current_user
from app.users.models import User
from app.plants.models import UserPlant  # Changed from Plant to UserPlant

router = APIRouter()

@router.get("/", response_model=List[UserPlant])
async def get_plants(current_user: User = Depends(get_current_user)):
    # Print for debugging
    print(f"Current user ID: {current_user.id}, type: {type(current_user.id)}")
    
    # Get all plants for the current user
    # Now using userplants collection instead of plants
    plants = list(db.userplants.find({"user_id": str(current_user.id)}))
    
    # Print for debugging
    print(f"Found {len(plants)} plants")
    
    # Convert ObjectId to string for each plant
    for plant in plants:
        plant["_id"] = str(plant["_id"])
    
    return plants

@router.get("/{plant_id}", response_model=UserPlant)
async def get_plant(
    plant_id: str,
    current_user: User = Depends(get_current_user)
):
    # Get a specific plant by ID
    # Now using userplants collection
    plant = db.userplants.find_one({
        "_id": ObjectId(plant_id),
        "user_id": str(current_user.id)
    })
    
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    # Convert ObjectId to string
    plant["_id"] = str(plant["_id"])
    
    return plant

@router.post("/", response_model=Dict[str, Any])
async def create_plant(
    plant_data: Dict[str, Any],  # Changed to Dict to accept arbitrary data including image_data
    current_user: User = Depends(get_current_user)
):
    # Extract the image data if it exists
    image_data = plant_data.pop("image_data", None)
    
    # Handle image processing if provided
    image_url = ""
    if image_data:
        try:
            # Create directory for uploaded images if it doesn't exist
            upload_dir = "static/uploads/plants"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Create a unique filename
            filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            file_path = os.path.join(upload_dir, filename)
            
            # Handle base64 image data
            # Check if it includes the "data:image" prefix
            if isinstance(image_data, str) and "," in image_data:
                # Split at the first comma to get just the base64 part
                image_data = image_data.split(",", 1)[1]
                
            # Save the image file
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(image_data))
                
            # Store the relative URL path
            image_url = f"/static/uploads/plants/{filename}"
            print(f"Image saved to {file_path}")
            
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            # Continue even if image saving fails
    
    # Remove the _id field if it's None
    if plant_data.get("_id") is None:
        plant_data.pop("_id", None)
    
    # Set user_id to current user's ID
    plant_data["user_id"] = str(current_user.id)
    
    # Set the image URL if we saved an image
    if image_url:
        plant_data["image_url"] = image_url
    
    # Insert the plant into userplants collection
    result = db.userplants.insert_one(plant_data)
    
    # Update the user's plants list
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$push": {"plants": str(result.inserted_id)}}
    )
    
    # Fetch the created plant and convert _id to string
    created_plant = db.userplants.find_one({"_id": result.inserted_id})
    if created_plant:
        created_plant["_id"] = str(created_plant["_id"])
    
    return {"success": True, "plant_id": str(result.inserted_id), "plant_data": created_plant}

@router.delete("/{plant_id}", response_model=dict)
async def delete_plant(
    plant_id: str,
    current_user: User = Depends(get_current_user)
):
    # Get the plant to ensure it belongs to the user
    plant = db.userplants.find_one({  # Changed from plants to userplants
        "_id": ObjectId(plant_id),
        "user_id": str(current_user.id)
    })
    
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    # If plant has an image URL, try to delete the file
    if "image_url" in plant and plant["image_url"]:
        try:
            # Get the file path from the URL
            file_path = plant["image_url"].lstrip("/")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted image file: {file_path}")
        except Exception as e:
            print(f"Error deleting image file: {str(e)}")
    
    # Remove the plant from the userplants collection
    db.userplants.delete_one({"_id": ObjectId(plant_id)})
    
    # Remove the plant ID from the user's plants list
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"plants": plant_id}}
    )
    
    return {"success": True}