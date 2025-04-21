from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Annotated, Any
from datetime import datetime

# Custom type for handling MongoDB ObjectId
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ])

    @classmethod
    def validate(cls, value):
        if isinstance(value, ObjectId):
            return value
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    plants: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @field_serializer('id')
    def serialize_id(self, id: PyObjectId) -> str:
        # Convert ObjectId to string for JSON serialization
        return str(id)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "_id": "123456789012345678901234",
                "username": "example_user",
                "hashed_password": "hashedpassword",
                "plants": [],
            }
        }
    }

class User(UserBase):
    id: str = Field(alias="_id")
    plants: List[str] = []
    
    model_config = {
        "populate_by_name": True
    }

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None