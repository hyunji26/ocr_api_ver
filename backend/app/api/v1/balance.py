from fastapi import APIRouter, Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta, date
from jwt import encode, decode  # PyJWT 대신 jwt를 직접 import
from sqlalchemy import select, func
import logging

from app.database import get_db
from app.models.balance import Meal, User
from app.services.balance.balance_service import BalanceService
from app.schemas.balance import MealCreate, BalanceResponse, UserCreate, Token, BalanceCreate, Balance, DailyBalance

# 로거 설정
logger = logging.getLogger(__name__)

# JWT 설정
SECRET_KEY = "your-secret-key"  # 실제 운영환경에서는 환경변수로 관리해야 함
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24시간으로 변경

router = APIRouter(prefix="/balance", tags=["Balance"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/balance/token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Union[str, int] = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        # 문자열을 정수로 변환
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/token")
async def login_for_access_token(db: Session = Depends(get_db)):
    """간단한 로그인을 위한 임시 엔드포인트"""
    try:
        logger.info("로그인 시도")
        # 새 사용자 생성
        user = User(daily_calorie_goal=2000)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"새 사용자 생성됨: ID {user.id}")
        
        # 토큰 생성
        access_token = create_access_token(data={"sub": str(user.id)})
        logger.info("토큰 생성 완료")
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "daily_calorie_goal": user.daily_calorie_goal
        }
        logger.info(f"응답 데이터: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user or generate token: {str(e)}"
        )

@router.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """새로운 사용자를 등록합니다."""
    db_user = User(daily_calorie_goal=user.daily_calorie_goal or 2000)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        # 토큰 생성
        access_token = create_access_token(data={"sub": str(db_user.id)})
        return {"access_token": access_token, "token_type": "bearer", "user_id": db_user.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.get("/stats")
async def get_balance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """인증된 사용자의 영양 밸런스 통계를 조회합니다."""
    try:
        balance_service = BalanceService(db)
        # 오늘의 식사 기록 조회
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        today_meals = db.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.timestamp >= start_of_day,
            Meal.timestamp <= end_of_day
        ).all()
        
        # 오늘의 총 영양소 계산
        if not today_meals:
            return {
                "balance_score": None,
                "total_calories": None,
                "daily_calorie_goal": current_user.daily_calorie_goal,
                "highlight": "",
                "needs_improvement": "",
                "nutrients": {
                    'carbohydrates': None,
                    'protein': None,
                    'fat': None
                }
            }
            
        total_nutrients = {
            'carbohydrates': float(sum(getattr(meal, 'carbohydrates', 0) or 0 for meal in today_meals)),
            'protein': float(sum(getattr(meal, 'protein', 0) or 0 for meal in today_meals)),
            'fat': float(sum(getattr(meal, 'fat', 0) or 0 for meal in today_meals))
        }
        
        # 밸런스 점수 계산
        balance_score = balance_service.calculate_balance_score(total_nutrients)
        
        # 영양소 분석
        nutrient_analysis = balance_service.analyze_nutrients(total_nutrients)
        
        # 총 칼로리
        total_calories = sum(meal.calories for meal in today_meals)
        
        return {
            "balance_score": balance_score,
            "total_calories": total_calories,
            "daily_calorie_goal": current_user.daily_calorie_goal,
            "highlight": nutrient_analysis["highlight"],
            "needs_improvement": nutrient_analysis["needsImprovement"],
            "nutrients": total_nutrients
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meals")
async def get_meals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """인증된 사용자의 오늘 식사 기록을 조회합니다."""
    try:
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        # 오늘의 모든 식사 기록 조회
        meals = db.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.timestamp >= start_of_day,
            Meal.timestamp <= end_of_day
        ).all()

        # 식사 타입별로 그룹화
        meal_groups = {
            'breakfast': [],
            'lunch': [],
            'dinner': []
        }

        for meal in meals:
            meal_type = meal.meal_type.lower()
            if meal_type in meal_groups:
                meal_groups[meal_type].append({
                    'name': meal.food_name or '식사',
                    'calories': float(str(meal.calories or 0)),
                    'nutrients': {
                        'carbohydrates': float(str(meal.carbohydrates or 0)),
                        'protein': float(str(meal.protein or 0)),
                        'fat': float(str(meal.fat or 0))
                    }
                })

        return meal_groups

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meals")
async def add_meal(
    meal: MealCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """인증된 사용자의 새로운 식사 기록을 추가합니다."""
    try:
        new_meal = Meal(
            user_id=current_user.id,
            meal_type=meal.meal_type,
            food_name=meal.food_name,
            calories=meal.calories,
            carbohydrates=meal.carbohydrates,
            protein=meal.protein,
            fat=meal.fat
        )
        
        db.add(new_meal)
        try:
            db.commit()
            db.refresh(new_meal)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save meal: {str(e)}")
        
        return {"message": "Meal added successfully", "meal_id": new_meal.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/balance", response_model=Balance)
def create_balance(balance: BalanceCreate, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.create_balance(balance)

@router.get("/balance/monthly/{user_id}/{year}/{month}", response_model=dict)
def get_monthly_balance(user_id: int, year: int, month: int, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.get_monthly_balance(user_id, year, month)

@router.get("/balance/daily/{user_id}/{year}/{month}/{day}", response_model=dict)
def get_daily_balance(user_id: int, year: int, month: int, day: int, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.get_daily_balance(user_id, year, month, day)

@router.get("/balance/stats/{user_id}", response_model=dict)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.get_user_stats(user_id)

@router.get("/balance/streak/{user_id}", response_model=dict)
def get_user_streak(user_id: int, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.get_user_streak(user_id) 