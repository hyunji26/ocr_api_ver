from pydantic import BaseModel
from typing import Dict

class NutrientInfo(BaseModel):
    amount: float
    unit: str
    daily_value: float

class FoodRecognitionResponse(BaseModel):
    name: str
    calories: int
    nutrients: Dict[str, NutrientInfo] 