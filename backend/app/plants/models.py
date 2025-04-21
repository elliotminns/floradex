from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from bson import ObjectId

# Create a simple serializable ObjectId helper class
class PydanticObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_cache):
        return {"type": "string"}

# Renamed from Plant to UserPlant
class UserPlant(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    type: str
    user_id: str
    date_added: str
    name: str
    confidence: float
    all_predictions: List[Dict[str, Any]] = []
    species_id: Optional[str] = None  # New field to reference plant species
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

# New model for plant species
class PlantSpecies(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    care_instructions: str
    watering_frequency: str
    sunlight_requirements: str
    humidity: str = "Medium"
    temperature: str = "65-75°F (18-24°C)"
    fertilization: str = "As needed"
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }