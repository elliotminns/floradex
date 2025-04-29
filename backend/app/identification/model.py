import requests
import logging
import os
from dotenv import load_dotenv
from app.identification.perenual_api import perenual_api

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
        else:
            # Log that we found the API key (but only show a prefix for security)
            api_key_prefix = self.api_key[:4] if len(self.api_key) > 4 else "****"
            logger.info(f"PlantNet API key found with prefix: {api_key_prefix}***")
            logger.info(f"PlantNet API URL: {self.api_url}")
    
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
                    scientific_name_with_author = prediction.get('species', {}).get('scientificName', '')
                    common_names = prediction.get('species', {}).get('commonNames', [])
                    genus = prediction.get('species', {}).get('genus', {}).get('scientificNameWithoutAuthor', '')
                    family = prediction.get('species', {}).get('family', {}).get('scientificNameWithoutAuthor', '')
                    
                    # Use common name if available, otherwise use scientific name
                    display_name = common_names[0] if common_names else scientific_name
                    
                    confidence = prediction.get('score', 0)
                    
                    predictions.append({
                        "plant_type": display_name,
                        "scientific_name": scientific_name,
                        "scientific_name_with_author": scientific_name_with_author,
                        "genus": genus,
                        "family": family,
                        "common_names": common_names,
                        "confidence": confidence
                    })
                
                # Sort predictions by confidence
                predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
                
                # Get the top prediction
                top_prediction = predictions[0]
                plant_type = top_prediction["plant_type"]
                scientific_name = top_prediction["scientific_name"]
                confidence = top_prediction["confidence"]
                
                # Create a list of search terms to try with Perenual API, in order of preference
                search_terms = []
                
                # Add common names from the top prediction first (if available)
                if top_prediction.get("common_names"):
                    search_terms.extend(top_prediction["common_names"])
                
                # Add the primary display name if not already in the list
                if plant_type not in search_terms:
                    search_terms.append(plant_type)
                
                # Add scientific name without author
                if scientific_name and scientific_name not in search_terms:
                    search_terms.append(scientific_name)
                
                # Add genus (which might get broader matches)
                if top_prediction.get("genus") and top_prediction["genus"] not in search_terms:
                    search_terms.append(top_prediction["genus"])
                
                # Log all the search terms we'll try
                logger.info(f"Will try the following search terms with Perenual API: {search_terms}")
                
                # Try each search term with Perenual API until we get a match
                care_details = None
                used_search_term = None
                
                for term in search_terms:
                    try:
                        logger.info(f"Trying to find care details for '{term}' with Perenual API")
                        care_details = perenual_api.get_plant_care_details(plant_name=term)
                        
                        # If we found valid care details, use this term and break the loop
                        if care_details:
                            # Check for default values that would indicate the API didn't have specific data
                            is_default = (
                                care_details.get("care_instructions") == "General care instructions not available" or
                                care_details.get("care_instructions") == "General care instructions for this plant" or
                                care_details.get("watering_frequency") == "Check specific requirements for this species"
                            )
                            
                            if not is_default:
                                used_search_term = term
                                logger.info(f"Successfully found care details using search term: '{term}'")
                                break
                            else:
                                logger.info(f"Found only default care details for '{term}', trying next term")
                        else:
                            logger.info(f"No care details found for '{term}', trying next term")
                    except Exception as e:
                        logger.error(f"Error searching Perenual API with term '{term}': {str(e)}")
                        # Continue trying other terms
                
                # If no care details found with any term, use default
                if not care_details or not used_search_term:
                    logger.warning(f"Could not find specific care details with any search term. Using default care info.")
                    care_details = perenual_api._get_default_care_info(plant_type)
                    used_search_term = plant_type
                
                # Prepare the response
                response = {
                    "plant_type": plant_type,
                    "scientific_name": scientific_name,
                    "confidence": confidence,
                    "all_predictions": predictions[:3],  # Return top 3 predictions
                    "search_terms_tried": search_terms,  # Include all search terms that were attempted
                    "search_term_matched": used_search_term,  # Term that matched in Perenual API
                    # Include care details from the Perenual API
                    "care_info": {
                        "care_instructions": care_details.get("care_instructions", "No care instructions available"),
                        "watering_frequency": care_details.get("watering_frequency", "Not specified"),
                        "sunlight_requirements": care_details.get("sunlight_requirements", "Not specified"),
                        "humidity": care_details.get("humidity", "Not specified"),
                        "temperature": care_details.get("temperature", "Not specified"),
                        "fertilization": care_details.get("fertilization", "Not specified"),
                        "description": care_details.get("description", "Not available"),
                        "perenual_image_url": care_details.get("image_url")
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