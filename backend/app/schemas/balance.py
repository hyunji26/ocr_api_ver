from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from enum import Enum

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"

class MealCreate(BaseModel):
    meal_type: MealType
    calories: float
    carbohydrates: float
    protein: float
    fat: float
    
    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    balance_score: int
    total_calories: float
    daily_calorie_goal: int
    highlight: str
    needs_improvement: str
    nutrients: Dict[str, float]
    meal_type: Optional[MealType] = None
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    daily_calorie_goal: Optional[int] = 2000

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int 