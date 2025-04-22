from fastapi import APIRouter, Depends, HTTPException
from app.auth.utils import get_current_user
from app.users.models import User
from app.config import db
from bson.objectid import ObjectId
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{plant_type}", response_model=dict)
async def get_plant_species_info(
    plant_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get care information for a specific plant species by its type/name.
    """
    try:
        logger.info(f"Looking up care info for plant type: {plant_type}")
        
        # Check for common plant types directly (for demo/development)
        plant_ids = {
            "Monstera Deliciosa": "6806329af92580246102ffa2",
            "Snake Plant": "6806329af92580246102ffa3",
            "Fiddle Leaf Fig": "68076b87618b092b279258b7"
        }
        
        # Try to find a direct match
        if plant_type in plant_ids:
            plant_id = plant_ids[plant_type]
            logger.info(f"Found direct match with ID: {plant_id}")
            
            # Look up the plant species by ID
            plant_species = db.plantspecies.find_one({"_id": ObjectId(plant_id)})
            
            if plant_species:
                # Convert ObjectId to string for JSON serialization
                plant_species["_id"] = str(plant_species["_id"])
                logger.info(f"Returning plant species info: {plant_species}")
                return plant_species
        
        # If no direct match, try to search by name (case-insensitive)
        logger.info(f"No direct match, searching by name")
        plant_species = db.plantspecies.find_one({"name": {"$regex": f"^{plant_type}$", "$options": "i"}})
        
        if plant_species:
            # Convert ObjectId to string for JSON serialization
            plant_species["_id"] = str(plant_species["_id"])
            logger.info(f"Found by name search: {plant_species}")
            return plant_species
            
        # If still not found, return a 404
        logger.warning(f"Plant species not found: {plant_type}")
        raise HTTPException(
            status_code=404,
            detail=f"Plant species not found: {plant_type}"
        )
        
    except Exception as e:
        logger.error(f"Error in get_plant_species_info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve plant species info: {str(e)}"
        )