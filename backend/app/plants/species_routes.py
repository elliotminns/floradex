from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from bson.objectid import ObjectId

from app.config import db
from app.auth.utils import get_current_user
from app.users.models import User
from app.plants.models import PlantSpecies

router = APIRouter()

@router.get("/", response_model=List[PlantSpecies])
async def get_plant_species(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all plant species, with optional filter by name"""
    # Build query
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive search
    
    # Get plant species from the plantspecies collection
    species_list = list(db.plantspecies.find(query))
    
    # Convert ObjectId to string for each species
    for species in species_list:
        species["_id"] = str(species["_id"])
    
    return species_list

@router.get("/{species_id}", response_model=PlantSpecies)
async def get_plant_species_by_id(
    species_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific plant species by ID"""
    # Get a specific plant species by ID
    species = db.plantspecies.find_one({"_id": ObjectId(species_id)})
    
    if not species:
        raise HTTPException(status_code=404, detail="Plant species not found")
    
    # Convert ObjectId to string
    species["_id"] = str(species["_id"])
    
    return species