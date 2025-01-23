from pydantic import BaseModel, validator, ValidationError
from typing import Literal,List

# Define the allowed values as a Literal type
ALLOWED_VALUES = [
    'gemini-1.0-pro-latest', 'gemini-1.0-pro', 'gemini-pro', 'gemini-1.0-pro-001', 
    'gemini-1.0-pro-vision-latest', 'gemini-pro-vision', 'gemini-1.5-pro-latest', 
    'gemini-1.5-pro-001', 'gemini-1.5-pro-002', 'gemini-1.5-pro', 'gemini-1.5-pro-exp-0801', 
    'gemini-1.5-pro-exp-0827', 'gemini-1.5-flash-latest', 'gemini-1.5-flash-001', 
    'gemini-1.5-flash-001-tuning', 'gemini-1.5-flash', 'gemini-1.5-flash-exp-0827', 
    'gemini-1.5-flash-002', 'gemini-1.5-flash-8b', 'gemini-1.5-flash-8b-001', 
    'gemini-1.5-flash-8b-latest', 'gemini-1.5-flash-8b-exp-0827', 'gemini-1.5-flash-8b-exp-0924', 
    'gemini-2.0-flash-exp', 'gemini-exp-1206', 'gemini-exp-1121', 'gemini-exp-1114', 
    'gemini-2.0-flash-thinking-exp-01-21', 'gemini-2.0-flash-thinking-exp', 
    'gemini-2.0-flash-thinking-exp-1219', 'learnlm-1.5-pro-experimental'
]

class Model(BaseModel):
    model_name: str 

    # Custom validator to ensure the field is within the allowed values
    @validator('model_name')
    def validate_model_name(cls, v):
        if v not in ALLOWED_VALUES:
            raise ValueError(f"Invalid model name '{v}'. Must be one of: {', '.join(ALLOWED_VALUES)}")
        return v


class FileNames(BaseModel):
    files: List = []

