import os
import requests
import logging
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerenualAPI:
    def __init__(self):
        # Perenual API configuration
        self.api_key = os.getenv("PERENUAL_API_KEY")
        self.base_url = "https://perenual.com/api"
        
        if not self.api_key:
            logger.warning("Perenual API key not found in environment variables! Make sure PERENUAL_API_KEY is set in your .env file.")
        else:
            # Log that we found the API key (but only show a prefix for security)
            api_key_prefix = self.api_key[:4] if len(self.api_key) > 4 else "****"
            logger.info(f"Perenual API key found with prefix: {api_key_prefix}***")
            logger.info(f"Base URL set to: {self.base_url}")
            
        # Test API connectivity
        try:
            self._test_api_connectivity()
        except Exception as e:
            logger.error(f"Failed to connect to Perenual API: {str(e)}")
            
    def _test_api_connectivity(self):
        """Test if the API key works by making a simple request"""
        if not self.api_key:
            logger.error("Cannot test API connectivity without an API key")
            return False
            
        try:
            # Make a simple request to check if the API key works
            params = {
                'key': self.api_key,
                'q': 'test'  # Simple search term
            }
            
            logger.info("Testing Perenual API connectivity...")
            response = requests.get(
                f"{self.base_url}/species-list",
                params=params
            )
            
            if response.status_code == 200:
                logger.info("✅ Successfully connected to Perenual API!")
                return True
            else:
                logger.error(f"❌ Failed to connect to Perenual API: {response.status_code} - {response.text}")
                if "Missing/Issue with API Key" in response.text:
                    logger.error("The API key appears to be invalid or not recognized by Perenual")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing API connectivity: {str(e)}")
            return False
    
    def search_plant_by_name(self, plant_name):
        """Search for plants by name and return matching results"""
        if not self.api_key:
            raise Exception("Perenual API key not configured")
        
        try:
            # Clean up the plant name - remove extra spaces, punctuation, etc.
            cleaned_name = self._clean_plant_name(plant_name)
            
            logger.info(f"Searching Perenual API for plant: {plant_name}")
            
            # Try different variations of the name for better matching
            search_variations = self._generate_search_variations(plant_name)
            
            for search_term in search_variations:
                logger.info(f"Trying search variation: {search_term}")
                
                # Set up the request parameters - make sure the API key param name is correct
                params = {
                    'key': self.api_key,
                    'q': search_term
                }
                
                # Log the URL we're calling (without the full API key for security)
                api_key_prefix = self.api_key[:4] if self.api_key and len(self.api_key) > 4 else "****"
                logger.info(f"Calling Perenual API with key prefix: {api_key_prefix}***")
                
                # Make the API request
                response = requests.get(
                    f"{self.base_url}/species-list",
                    params=params
                )
                
                # Check if the request was successful
                if response.status_code != 200:
                    logger.error(f"Perenual API search request failed with status code {response.status_code}: {response.text}")
                    
                    # Special handling for API key issues
                    if response.status_code == 404 and "Missing/Issue with API Key" in response.text:
                        logger.error("API key issue detected. Please check your Perenual API key configuration.")
                        raise Exception("Invalid or missing Perenual API key. Please check your .env file.")
                        
                    if response.status_code == 429:  # Too Many Requests
                        break  # Stop trying variations to avoid more rate limit issues
                    continue  # Try next variation
                
                # Parse the response
                result = response.json()
                
                # Check if we got any results
                if result.get('data') and len(result['data']) > 0:
                    logger.info(f"Found {len(result['data'])} matching plants in Perenual API using '{search_term}'")
                    
                    # Return the first (most relevant) result's ID
                    plant_id = result['data'][0]['id']
                    return plant_id
                else:
                    logger.warning(f"No plants found matching '{search_term}' in Perenual API")
            
            # No results found with any variation
            return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Perenual API search request error: {str(e)}")
            raise Exception(f"Perenual API connection error: {str(e)}")
    
    def get_plant_care_details(self, plant_id=None, plant_name=None):
        """Get detailed care information for a plant by ID or name"""
        if not self.api_key:
            raise Exception("Perenual API key not configured")
        
        try:
            # If we don't have an ID but have a name, search for the plant first
            if not plant_id and plant_name:
                plant_id = self.search_plant_by_name(plant_name)
                
                if not plant_id:
                    # If we still don't have an ID, return default care info
                    logger.warning(f"Could not find plant ID for '{plant_name}'")
                    return self._get_default_care_info(plant_name)
            
            # Ensure we have a plant ID to lookup
            if not plant_id:
                raise Exception("Plant ID is required for care details lookup")
                
            logger.info(f"Getting care details for plant ID: {plant_id}")
            
            # Set up the request parameters
            params = {
                'key': self.api_key,
            }
            
            # Log the URL we're calling (without the full API key for security)
            api_key_prefix = self.api_key[:4] if self.api_key and len(self.api_key) > 4 else "****"
            logger.info(f"Calling Perenual API with key prefix: {api_key_prefix}***")
            
            # Make the API request for species details
            response = requests.get(
                f"{self.base_url}/species/details/{plant_id}",
                params=params
            )
            
            # Check if the request was successful
            if response.status_code != 200:
                logger.error(f"Perenual API details request failed with status code {response.status_code}: {response.text}")
                
                # Special handling for API key issues
                if response.status_code == 404 and "Missing/Issue with API Key" in response.text:
                    logger.error("API key issue detected. Please check your Perenual API key configuration.")
                    raise Exception("Invalid or missing Perenual API key. Please check your .env file.")
                
                if response.status_code == 429:  # Too Many Requests
                    return self._get_default_care_info(plant_name or f"Plant ID: {plant_id}")
                else:
                    raise Exception(f"Perenual API error: {response.status_code} - {response.text}")
            
            # Parse the response
            result = response.json()
            
            # Extract care info from the API response
            care_info = self._extract_care_info(result)
            logger.info(f"Successfully retrieved care details for plant ID: {plant_id}")
            
            return care_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Perenual API details request error: {str(e)}")
            # Return default care info if we encounter an error
            return self._get_default_care_info(plant_name or f"Plant ID: {plant_id}")
        except Exception as e:
            logger.error(f"Error getting plant care details: {str(e)}")
            # Return default care info if we encounter an error
            return self._get_default_care_info(plant_name or f"Plant ID: {plant_id}")
            
    def _clean_plant_name(self, plant_name):
        """Clean up plant name for better search matching"""
        if not plant_name:
            return ""
        
        # Remove punctuation and extra spaces
        cleaned = re.sub(r'[^\w\s]', ' ', plant_name)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Convert to lowercase
        cleaned = cleaned.lower()
        
        return cleaned
        
    def _generate_search_variations(self, plant_name):
        """Generate variations of plant name for better search matching"""
        variations = []
        
        # Original name first
        if plant_name:
            variations.append(plant_name)
        
        # Cleaned name
        cleaned = self._clean_plant_name(plant_name)
        if cleaned and cleaned != plant_name:
            variations.append(cleaned)
        
        # Try removing common prefixes/suffixes
        words = cleaned.split()
        
        # Remove common cultivar indicators
        if len(words) > 1:
            if words[-1].lower() in ['plant', 'tree', 'bush', 'shrub', 'vine', 'herb']:
                variations.append(' '.join(words[:-1]))
            
            # Remove 'common', 'wild', etc. at the beginning
            if words[0].lower() in ['common', 'wild', 'dwarf', 'giant', 'japanese', 'chinese', 'european', 'american']:
                variations.append(' '.join(words[1:]))
        
        # If it might be a scientific name (contains two words, first capitalized)
        parts = plant_name.split()
        if len(parts) >= 2:
            # Try just the genus (first word)
            genus = parts[0]
            if genus[0].isupper():
                variations.append(genus)
        
        return list(dict.fromkeys(variations))  # Remove duplicates while preserving order
    
    def _extract_care_info(self, api_response):
        """Extract and format care information from the API response"""
        try:
            # Debug log to see what we're getting from the API
            logger.debug(f"API response structure: {type(api_response)}")
            
            # Check if we have a valid response
            if not isinstance(api_response, dict):
                logger.error(f"Invalid API response format: {type(api_response)}")
                return self._get_default_care_info("Unknown Plant")
            
            # Extract scientific name safely
            scientific_name = "Unknown"
            if api_response.get('scientific_name'):
                if isinstance(api_response['scientific_name'], list) and len(api_response['scientific_name']) > 0:
                    scientific_name = api_response['scientific_name'][0]
                elif isinstance(api_response['scientific_name'], str):
                    scientific_name = api_response['scientific_name']
            
            # Default values in case the API doesn't provide certain fields
            return {
                "name": api_response.get('common_name', 'Unknown Plant'),
                "scientific_name": scientific_name,
                "care_instructions": self._format_care_instructions(api_response),
                "watering_frequency": self._extract_watering(api_response),
                "sunlight_requirements": self._extract_sunlight(api_response),
                "humidity": self._extract_humidity(api_response),
                "temperature": self._extract_temperature(api_response),
                "fertilization": api_response.get('care_level', 'Medium'),
                "description": api_response.get('description', 'No description available'),
                "image_url": self._extract_image_url(api_response)
            }
        except Exception as e:
            logger.error(f"Error extracting care info from API response: {str(e)}")
            return self._get_default_care_info("Unknown Plant")
            
    def _format_care_instructions(self, api_response):
        """Format general care instructions from various API fields"""
        try:
            instructions = []
            
            if api_response.get('description'):
                instructions.append(api_response['description'])
            
            if api_response.get('care_level'):
                instructions.append(f"Care Level: {api_response['care_level']}")
                
            return " ".join(instructions) or "General care instructions not available"
        except Exception as e:
            logger.error(f"Error formatting care instructions: {str(e)}")
            return "General care instructions not available"
    
    def _extract_watering(self, api_response):
        """Extract watering information from API response"""
        try:
            watering = api_response.get('watering')
            if watering:
                return watering
            return "Check specific requirements for this species"
        except Exception as e:
            logger.error(f"Error extracting watering information: {str(e)}")
            return "Check specific requirements for this species"
    
    def _extract_sunlight(self, api_response):
        """Extract sunlight requirements from API response"""
        try:
            sunlight = api_response.get('sunlight')
            if sunlight and isinstance(sunlight, list) and sunlight:
                return ", ".join(sunlight)
            return "Medium indirect light"
        except Exception as e:
            logger.error(f"Error extracting sunlight information: {str(e)}")
            return "Medium indirect light"
    
    def _extract_humidity(self, api_response):
        """Extract humidity information from API response"""
        try:
            # Perenual API may not provide direct humidity values
            return api_response.get('humidity', 'Average')
        except Exception as e:
            logger.error(f"Error extracting humidity information: {str(e)}")
            return "Average"
    
    def _extract_temperature(self, api_response):
        """Extract temperature information from API response and convert to Celsius"""
        try:
            # Get hardiness data from API response
            hardiness = api_response.get('hardiness', {})
            
            # Check if hardiness is a dictionary with min/max values
            if isinstance(hardiness, dict) and 'min' in hardiness and 'max' in hardiness:
                min_temp_f = hardiness.get('min')
                max_temp_f = hardiness.get('max')
                
                # Convert string values to integers if needed
                if min_temp_f is not None and max_temp_f is not None:
                    try:
                        # Try to convert to integers if they're strings
                        if isinstance(min_temp_f, str):
                            min_temp_f = int(min_temp_f)
                        if isinstance(max_temp_f, str):
                            max_temp_f = int(max_temp_f)
                            
                        # Convert Fahrenheit to Celsius
                        min_temp_c = round((min_temp_f - 32) * 5/9)
                        max_temp_c = round((max_temp_f - 32) * 5/9)
                        return f"{min_temp_c}-{max_temp_c}°C ({min_temp_f}-{max_temp_f}°F)"
                    except (ValueError, TypeError):
                        logger.error(f"Could not convert temperature values: min={min_temp_f}, max={max_temp_f}")
            
            # If we reach here, either hardiness data is missing or conversion failed
            return "18-24°C (65-75°F)"  # Default
        except Exception as e:
            logger.error(f"Error extracting temperature information: {str(e)}")
            return "18-24°C (65-75°F)"  # Default on error
    
    def _extract_image_url(self, api_response):
        """Extract image URL from API response"""
        try:
            if api_response.get('default_image') and api_response['default_image'].get('original_url'):
                return api_response['default_image']['original_url']
            return None
        except Exception as e:
            logger.error(f"Error extracting image URL: {str(e)}")
            return None
    
    def _get_default_care_info(self, plant_name):
        """Return default care information when API lookup fails"""
        return {
            "name": plant_name,
            "scientific_name": "Unknown",
            "care_instructions": "General care instructions for this plant",
            "watering_frequency": "Check specific requirements for this species",
            "sunlight_requirements": "Medium indirect light",
            "humidity": "Average",
            "temperature": "18-24°C (65-75°F)",
            "fertilization": "As needed during growing season",
            "description": "No description available",
            "image_url": None
        }

# Create a singleton instance
perenual_api = PerenualAPI()