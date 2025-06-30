from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    meal_type = Column(SQLAlchemyEnum(MealType), nullable=False)
    food_name = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(KST))
    calories = Column(Float)
    carbohydrates = Column(Float)
    protein = Column(Float)
    fat = Column(Float)

    user = relationship("User", back_populates="meals")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    daily_calorie_goal = Column(Integer, default=2000)
    created_at = Column(DateTime, default=lambda: datetime.now(KST))
    meals = relationship("Meal", back_populates="user") 