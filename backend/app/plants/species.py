from fastapi import APIRouter, Depends, HTTPException
from app.auth.utils import get_current_user
from app.users.models import User
from app.identification.perenual_api import perenual_api
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
    Get care information for a specific plant species by its type/name from Perenual API.
    """
    try:
        logger.info(f"Looking up care info for plant type: {plant_type}")
        
        try:
            # Use Perenual API to get care information by plant name
            care_info = perenual_api.get_plant_care_details(plant_name=plant_type)
            
            if care_info:
                # Format the response to match the expected schema
                return {
                    "name": care_info.get("name", plant_type),
                    "scientific_name": care_info.get("scientific_name", "Unknown"),
                    "care_instructions": care_info.get("care_instructions", "General care instructions for this plant"),
                    "watering_frequency": care_info.get("watering_frequency", "Check specific requirements for this species"),
                    "sunlight_requirements": care_info.get("sunlight_requirements", "Medium indirect light"),
                    "humidity": care_info.get("humidity", "Average"),
                    "temperature": care_info.get("temperature", "18-24°C (65-75°F)"),
                    "fertilization": care_info.get("fertilization", "As needed during growing season"),
                    "description": care_info.get("description", "No description available"),
                    "image_url": care_info.get("image_url")
                }
            else:
                # Return default information if no specific care info found
                logger.warning(f"No care info found for plant type: {plant_type}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Plant species not found: {plant_type}"
                )
                
        except Exception as e:
            logger.error(f"Error getting plant care info: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve plant species info: {str(e)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
    except Exception as e:
        logger.error(f"Error in get_plant_species_info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )