from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson.objectid import ObjectId

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

@router.post("/", response_model=UserPlant)
async def create_plant(
    plant_data: UserPlant,  # Changed from Plant to UserPlant
    current_user: User = Depends(get_current_user)
):
    # Convert the plant data to a dict
    plant_dict = plant_data.model_dump(by_alias=True)
    
    # Remove the _id field if it's None
    if plant_dict.get("_id") is None:
        plant_dict.pop("_id", None)
    
    # Set user_id to current user's ID
    plant_dict["user_id"] = str(current_user.id)
    
    # Insert the plant into userplants collection
    result = db.userplants.insert_one(plant_dict)
    
    # Update the user's plants list
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$push": {"plants": str(result.inserted_id)}}
    )
    
    # Fetch the created plant and convert _id to string
    created_plant = db.userplants.find_one({"_id": result.inserted_id})
    if created_plant:
        created_plant["_id"] = str(created_plant["_id"])
    
    return created_plant

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
    
    # Remove the plant from the userplants collection
    db.userplants.delete_one({"_id": ObjectId(plant_id)})
    
    # Remove the plant ID from the user's plants list
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"plants": plant_id}}
    )
    
    return {"success": True}