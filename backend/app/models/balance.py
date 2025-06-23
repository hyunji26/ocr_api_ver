from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from app.database import Base
import enum

class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    meal_type = Column(SQLAlchemyEnum(MealType), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    calories = Column(Float)
    carbohydrates = Column(Float)
    protein = Column(Float)
    fat = Column(Float)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    daily_calorie_goal = Column(Integer, default=2000)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 