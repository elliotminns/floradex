from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from app.auth.utils import get_current_user
from app.users.models import User
from app.identification.model import plant_identifier
from app.config import db
from bson.objectid import ObjectId
from datetime import datetime
import os
import logging
import json
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=dict)
async def identify_plant(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Processing plant identification request from user: {current_user.username}")
        
        # Read the image file
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="Empty image file"
            )
            
        logger.info(f"Image size: {len(image_bytes)} bytes")
        
        # Generate a unique filename
        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = f"static/uploads/plants/{filename}"
        
        # Save the image to your storage
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        # Generate URL for the saved image
        image_url = f"/static/uploads/plants/{filename}"
        logger.info(f"Image saved to {file_path}")
        
        try:
            # Identify the plant using PlantNet API
            logger.info("Calling PlantNet API via plant_identifier")
            result = plant_identifier.identify(image_bytes)
            
            # Add the image URL to the result
            result["image_url"] = image_url
            
            logger.info(f"Plant identified as {result.get('plant_type')} with {result.get('confidence')} confidence")
            return result
            
        except Exception as identification_error:
            # Handle specific identification errors
            logger.error(f"Plant identification error: {str(identification_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Plant identification failed: {str(identification_error)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process plant identification request: {str(e)}"
        )

@router.post("/identify-base64", response_model=dict)
async def identify_plant_base64(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    try:
        # Parse the request body
        body = await request.json()
        image_data = body.get("image_data")
        
        if not image_data:
            raise HTTPException(
                status_code=400,
                detail="No image data provided"
            )
            
        # Handle base64 image data
        # Check if it includes the "data:image" prefix and remove it
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
            
        # Decode the base64 image
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 image data: {str(e)}"
            )
            
        # Generate a unique filename
        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = f"static/uploads/plants/{filename}"
        
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
        
    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
    except Exception as e:
        logger.error(f"Base64 identification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process plant identification request: {str(e)}"
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
        
        # Format the date correctly
        current_date = datetime.now().isoformat()
        
        # Create a new plant entry with the image URL and care information
        plant = {
            "type": plant_type,
            "user_id": str(current_user.id),  # Ensure user_id is a string
            "date_added": current_date,
            "name": plant_data.get("name", plant_type),  # Use plant_type as default name
            "image_url": image_url,
            "confidence": plant_data.get("confidence", 0),
            "all_predictions": plant_data.get("all_predictions", []),
            # Store scientific name if available
            "scientific_name": plant_data.get("scientific_name", ""),
            # Store care information from the identification result
            "care_info": plant_data.get("care_info", {})
        }
        
        # Insert the plant into the userplants collection (note: not plants)
        result = db.userplants.insert_one(plant)
        plant_id = str(result.inserted_id)
        
        # Update the user's plants list
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$push": {"plants": plant_id}}
        )
        
        return {"success": True, "plant_id": plant_id}
    except Exception as e:
        logger.error(f"Add to collection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add plant to collection: {str(e)}"
        )