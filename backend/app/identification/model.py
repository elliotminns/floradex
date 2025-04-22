import random
from bson import ObjectId
from app.config import db  # Import the db instance directly from config

# In app/identification/model.py
class PlantIdentifier:
    def __init__(self):
        # Comment out model loading for now
        # self.model = tf.keras.models.load_model(MODEL_PATH)
        self.model = None
        
        # Define the plant IDs from your MongoDB collection
        self.plant_species_ids = {
            "Monstera Deliciosa": "6806329af92580246102ffa2",
            "Snake Plant": "6806329af92580246102ffa3",
            "Fiddle Leaf Fig": "68076b87618b092b279258b7"
        }
        
        # Use the db instance from app.config
        try:
            # Important: Don't check truthiness of MongoDB collections directly
            # Instead, just set the reference and check for None later
            self.plant_species_collection = db.plantspecies
            print("Using MongoDB collection from app config")
        except Exception as e:
            print(f"Error accessing plantspecies collection: {e}")
            self.plant_species_collection = None
    
    def _get_plant_details(self, plant_type):
        """Retrieve plant details from MongoDB based on plant type"""
        # Important: Check if the collection is None, not its truthiness
        if self.plant_species_collection is None:
            # If MongoDB connection failed, raise an error
            raise Exception("MongoDB collection unavailable")
                
        # Get the plant ID for the given plant type
        plant_id = self.plant_species_ids.get(plant_type)
        if not plant_id:
            raise Exception(f"No ID found for plant type: {plant_type}")
                
        # Query MongoDB for the plant details
        plant_details = self.plant_species_collection.find_one({"_id": ObjectId(plant_id)})
            
        if plant_details is None:
            raise Exception(f"No plant found with ID: {plant_id}")
                
        return plant_details
    
    def identify(self, image_bytes):
        """Simulate plant identification and return identification results with care info"""
        # Define mock prediction data
        mock_predictions = [
            {
                "predictions": [
                    {"plant_type": "Monstera Deliciosa", "confidence": 0.95},
                    {"plant_type": "Pothos", "confidence": 0.03},
                    {"plant_type": "Philodendron", "confidence": 0.02}
                ]
            },
            {
                "predictions": [
                    {"plant_type": "Fiddle Leaf Fig", "confidence": 0.88},
                    {"plant_type": "Rubber Plant", "confidence": 0.10},
                    {"plant_type": "Bird of Paradise", "confidence": 0.02}
                ]
            },
            {
                "predictions": [
                    {"plant_type": "Snake Plant", "confidence": 0.92},
                    {"plant_type": "Aloe Vera", "confidence": 0.05},
                    {"plant_type": "ZZ Plant", "confidence": 0.03}
                ]
            }
        ]
        
        try:
            # Choose a random prediction set
            prediction_set = random.choice(mock_predictions)
            
            # Get the top prediction (highest confidence)
            top_prediction = prediction_set["predictions"][0]
            plant_type = top_prediction["plant_type"]
            confidence = top_prediction["confidence"]
            
            # Get plant details from MongoDB
            plant_details = self._get_plant_details(plant_type)
            
            # Prepare the response
            response = {
                "plant_type": plant_type,
                "confidence": confidence,
                "all_predictions": prediction_set["predictions"],
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
            
            return response
        except Exception as e:
            # Better error handling with specific message
            print(f"Error in identify method: {str(e)}")
            raise Exception(f"Plant identification failed: {str(e)}")

# Create a singleton instance
plant_identifier = PlantIdentifier()