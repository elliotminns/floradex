import random

# In app/identification/model.py
class PlantIdentifier:
    def __init__(self):
        # Comment out model loading for now
        # self.model = tf.keras.models.load_model(MODEL_PATH)
        self.model = None
        
        # Define some mock plant types for simulation
        self.mock_plants = [
            {
                "plant_type": "Monstera Deliciosa",
                "confidence": 0.95,
                "all_predictions": [
                    {"plant_type": "Monstera Deliciosa", "confidence": 0.95},
                    {"plant_type": "Pothos", "confidence": 0.03},
                    {"plant_type": "Philodendron", "confidence": 0.02}
                ]
            },
            {
                "plant_type": "Fiddle Leaf Fig",
                "confidence": 0.88,
                "all_predictions": [
                    {"plant_type": "Fiddle Leaf Fig", "confidence": 0.88},
                    {"plant_type": "Rubber Plant", "confidence": 0.10},
                    {"plant_type": "Bird of Paradise", "confidence": 0.02}
                ]
            },
            {
                "plant_type": "Snake Plant",
                "confidence": 0.92,
                "all_predictions": [
                    {"plant_type": "Snake Plant", "confidence": 0.92},
                    {"plant_type": "Aloe Vera", "confidence": 0.05},
                    {"plant_type": "ZZ Plant", "confidence": 0.03}
                ]
            }
        ]
        
    def identify(self, image_bytes):
        # Return a random plant from our mock data
        return random.choice(self.mock_plants)

# Create a singleton instance
plant_identifier = PlantIdentifier()