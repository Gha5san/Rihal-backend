from bson import ObjectId
from pydantic import BaseModel, Field


""""
Scheme is still incomplete, it aims to improve the API documentation by 
defining a data model  with fields that have specific types, default values, and validation rules
which will improve the documentation.
"""

class PyObjectId(ObjectId):
    """This class to handle mongodb _id"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class GetAll(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str 
    upload_time: str 
    size: int 
    pages: int 
    
    class Config:
        # Set default values for the fields
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "_id": "64417eea84c474232a2c9ec8",
                "name": "simple.pdf",
                "upload_time": "2023-04-20 18:05:30.644889",
                "size": 377776,
                "pages": 1
            }
        }