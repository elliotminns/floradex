from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.auth.utils import get_current_user
from app.users.models import User
from app.identification.perenual_api import perenual_api
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_plant_species(
    name: Optional[str] = Query(None, description="Filter species by name"),
    current_user: User = Depends(get_current_user)
):
    """Get plant species from Perenual API with optional filter by name"""
    try:
        # We'll use the search functionality of the Perenual API
        logger.info(f"Searching for plant species with name: {name}")
        
        if not name or len(name.strip()) < 3:
            # Return a message that a search term of at least 3 characters is required
            return [
                {
                    "_id": "search_required",
                    "name": "Please provide a search term of at least 3 characters",
                    "care_instructions": "",
                    "watering_frequency": "",
                    "sunlight_requirements": "",
                    "humidity": "",
                    "temperature": "",
                    "fertilization": ""
                }
            ]
        
        # Use the Perenual API to search for plants
        try:
            # First get the plant ID from the search
            plant_id = perenual_api.search_plant_by_name(name)
            
            if plant_id:
                # Get the full details
                care_details = perenual_api.get_plant_care_details(plant_id=plant_id)
                
                # Format the response to match the expected schema
                return [
                    {
                        "_id": str(plant_id),  # Use the Perenual ID as our ID
                        "name": care_details.get("name", name),
                        "scientific_name": care_details.get("scientific_name", "Unknown"),
                        "care_instructions": care_details.get("care_instructions", ""),
                        "watering_frequency": care_details.get("watering_frequency", ""),
                        "sunlight_requirements": care_details.get("sunlight_requirements", ""),
                        "humidity": care_details.get("humidity", ""),
                        "temperature": care_details.get("temperature", ""),
                        "fertilization": care_details.get("fertilization", ""),
                        "description": care_details.get("description", ""),
                        "image_url": care_details.get("image_url")
                    }
                ]
            else:
                # No results found
                return [
                    {
                        "_id": "not_found",
                        "name": f"No plant species found matching '{name}'",
                        "care_instructions": "",
                        "watering_frequency": "",
                        "sunlight_requirements": "",
                        "humidity": "",
                        "temperature": "",
                        "fertilization": ""
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error searching Perenual API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search plant species: {str(e)}"
            )
    
    except Exception as e:
        logger.error(f"Error in get_plant_species: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get plant species: {str(e)}"
        )

@router.get("/{species_id}", response_model=Dict[str, Any])
async def get_plant_species_by_id(
    species_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific plant species by Perenual API ID"""
    try:
        logger.info(f"Getting plant species with ID: {species_id}")
        
        # Use the Perenual API to get plant details by ID
        try:
            # Check if the ID is one of our special IDs
            if species_id in ["search_required", "not_found"]:
                raise HTTPException(
                    status_code=404,
                    detail="Invalid plant species ID"
                )
                
            # Get the full details from Perenual API
            care_details = perenual_api.get_plant_care_details(plant_id=species_id)
            
            # Format the response to match the expected schema
            return {
                "_id": species_id,
                "name": care_details.get("name", "Unknown Plant"),
                "scientific_name": care_details.get("scientific_name", "Unknown"),
                "care_instructions": care_details.get("care_instructions", ""),
                "watering_frequency": care_details.get("watering_frequency", ""),
                "sunlight_requirements": care_details.get("sunlight_requirements", ""),
                "humidity": care_details.get("humidity", ""),
                "temperature": care_details.get("temperature", ""),
                "fertilization": care_details.get("fertilization", ""),
                "description": care_details.get("description", ""),
                "image_url": care_details.get("image_url")
            }
                
        except Exception as e:
            logger.error(f"Error getting plant details from Perenual API: {str(e)}")
            raise HTTPException(
                status_code=404,
                detail=f"Plant species not found: {str(e)}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
    except Exception as e:
        logger.error(f"Error in get_plant_species_by_id: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get plant species: {str(e)}"
        )