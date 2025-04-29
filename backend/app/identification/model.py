import requests
import logging
import os
from bson import ObjectId
from app.config import db
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PlantIdentifier:
    def __init__(self):
        # PlantNet API configuration
        self.api_key = os.getenv("PLANTNET_API_KEY")
        self.api_url = "https://my-api.plantnet.org/v2/identify/all"
        
        if not self.api_key:
            logger.warning("PlantNet API key not found in environment variables")
        
        # Use the db instance from app.config
        try:
            self.plant_species_collection = db.plantspecies
            logger.info("Connected to MongoDB plantspecies collection")
        except Exception as e:
            logger.error(f"Error accessing plantspecies collection: {e}")
            self.plant_species_collection = None
    
    def _get_plant_details(self, plant_type):
        """Retrieve plant details from MongoDB based on plant type"""
        if self.plant_species_collection is None:
            raise Exception("MongoDB collection unavailable")
        
        # First try direct lookup by name
        plant_details = self.plant_species_collection.find_one({"name": plant_type})
        if plant_details:
            logger.info(f"Found plant details for: {plant_type} (direct name lookup)")
            return plant_details
        
        # If not found directly, try case-insensitive search
        plant_details = self.plant_species_collection.find_one(
            {"name": {"$regex": f"^{plant_type}$", "$options": "i"}}
        )
        if plant_details:
            logger.info(f"Found plant details for: {plant_type} (case-insensitive lookup)")
            return plant_details
            
        # If no match found in database, return default info
        logger.warning(f"No plant details found for: {plant_type}")
        return {
            "name": plant_type,
            "care_instructions": "General care instructions for this plant",
            "watering_frequency": "Check specific requirements for this species",
            "sunlight_requirements": "Medium indirect light",
            "humidity": "Average",
            "temperature": "65-75°F (18-24°C)",
            "fertilization": "As needed during growing season"
        }
    
    def identify(self, image_bytes):
        """Identify plant using PlantNet API"""
        if not self.api_key:
            raise Exception("PlantNet API key not found in environment variables")
            
        try:
            logger.info("Preparing PlantNet API request")
            
            # Set up API parameters
            params = {
                'api-key': self.api_key,
            }
            
            # Prepare the image file for upload
            files = {
                'images': ('image.jpg', image_bytes, 'image/jpeg')
            }
            
            # Make the request to PlantNet API
            logger.info("Sending request to PlantNet API...")
            response = requests.post(
                self.api_url,
                params=params,
                files=files
            )
            
            # Check if the request was successful
            if response.status_code != 200:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                raise Exception(f"PlantNet API error: {response.status_code} - {response.text}")
                
            # Parse the response
            result = response.json()
            logger.info("Received response from PlantNet API")
            
            # Extract the top predictions
            predictions = []
            if 'results' in result and len(result['results']) > 0:
                for prediction in result['results']:
                    # Extract the scientific name and score
                    scientific_name = prediction.get('species', {}).get('scientificNameWithoutAuthor', '')
                    common_names = prediction.get('species', {}).get('commonNames', [])
                    
                    # Use common name if available, otherwise use scientific name
                    display_name = common_names[0] if common_names else scientific_name
                    
                    confidence = prediction.get('score', 0)
                    
                    predictions.append({
                        "plant_type": display_name,
                        "scientific_name": scientific_name,
                        "confidence": confidence
                    })
                
                # Sort predictions by confidence
                predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
                
                # Get the top prediction
                top_prediction = predictions[0]
                plant_type = top_prediction["plant_type"]
                confidence = top_prediction["confidence"]
                
                # Get plant details from MongoDB
                plant_details = self._get_plant_details(plant_type)
                
                # Prepare the response
                response = {
                    "plant_type": plant_type,
                    "scientific_name": top_prediction["scientific_name"],
                    "confidence": confidence,
                    "all_predictions": predictions[:3],  # Return top 3 predictions
                    # Include care details from the database
                    "care_info": {
                        "care_instructions": plant_details.get("care_instructions", "No care instructions available"),
                        "watering_frequency": plant_details.get("watering_frequency", "Not specified"),
                        "sunlight_requirements": plant_details.get("sunlight_requirements", "Not specified"),
                        "humidity": plant_details.get("humidity", "Not specified"),
                        "temperature": plant_details.get("temperature", "Not specified"),
                        "fertilization": plant_details.get("fertilization", "Not specified")
                    }
                }
                
                logger.info(f"Identified plant as {plant_type} with {confidence:.2f} confidence")
                return response
            else:
                raise Exception("No plant identification results returned from API")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"API connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in identify method: {str(e)}")
            raise Exception(f"Plant identification failed: {str(e)}")

# Create a singleton instance
plant_identifier = PlantIdentifier()