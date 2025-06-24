from pydantic import BaseModel, EmailStr
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

__all__ = ['BalanceCreate', 'Balance', 'DailyBalance', 'MealCreate', 'BalanceResponse', 'UserCreate', 'Token', 'UserProfile', 'UserProfileUpdate', 'UserLogin']

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"

class MealCreate(BaseModel):
    meal_type: MealType
    food_name: str
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
    email: EmailStr
    password: str
    name: str
    daily_calorie_goal: Optional[int] = 2000

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: Optional[str] = None

class BalanceCreate(BaseModel):
    user_id: int
    meal_type: str
    menu: str
    calories: float
    nutrients: Dict[str, float]
    meal_date: datetime
    weather: Optional[str] = None
    mood: Optional[str] = None
    exercise: Optional[bool] = False
    water_intake: Optional[float] = 0

class Balance(BalanceCreate):
    id: int

    class Config:
        from_attributes = True

class DailyBalance(BaseModel):
    date: datetime
    calories: float
    carbohydrates: float
    protein: float
    fat: float

class UserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    profile_image: Optional[str] = None
    daily_calorie_goal: Optional[int] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_image: Optional[str] = None
    daily_calorie_goal: Optional[int] = None 