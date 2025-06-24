from fastapi import APIRouter, Depends, HTTPException, Cookie, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta, date
from jwt import encode, decode
from sqlalchemy import select, func
import logging
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.balance import Meal, User
from app.services.balance.balance_service import BalanceService
from app.schemas.balance import MealCreate, BalanceResponse, UserCreate, Token, BalanceCreate, Balance, DailyBalance, UserProfile, UserProfileUpdate, UserLogin

# 로거 설정
logger = logging.getLogger(__name__)

# JWT 설정
SECRET_KEY = "your-secret-key"  # 실제 운영환경에서는 환경변수로 관리해야 함
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24시간

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/balance", tags=["Balance"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/balance/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(user_data: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인 및 토큰 발급"""
    try:
        logger.info(f"로그인 시도: {user_data.email}")
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )
        
        # 토큰 생성
        access_token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"로그인 성공: 사용자 ID {user.id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name
        }
        
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

@router.post("/register", response_model=Token)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """새로운 사용자를 등록합니다."""
    try:
        # 이메일 중복 확인
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=400,
                detail="이미 등록된 이메일입니다."
            )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)
        
        # 새 사용자 생성
        db_user = User(
            email=user.email,
            password_hash=hashed_password,
            name=user.name,
            daily_calorie_goal=user.daily_calorie_goal
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 토큰 생성
        access_token = create_access_token(data={"sub": str(db_user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": db_user.id,
            "name": db_user.name
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일입니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"사용자 등록 중 오류가 발생했습니다: {str(e)}"
        )

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
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """인증된 사용자의 특정 날짜 식사 기록을 조회합니다."""
    try:
        # 날짜가 제공되지 않으면 오늘 날짜 사용
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()

        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        # 해당 날짜의 모든 식사 기록 조회
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

@router.get("/monthly/{user_id}/{year}/{month}", response_model=dict)
async def get_monthly_balance(
    user_id: int,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """인증된 사용자의 월간 밸런스 통계를 조회합니다."""
    balance_service = BalanceService(db)
    return balance_service.get_monthly_balance(user_id, year, month)

# @router.get("/balance/daily/{user_id}/{year}/{month}/{day}", response_model=dict)
# def get_daily_balance(user_id: int, year: int, month: int, day: int, db: Session = Depends(get_db)):
#     balance_service = BalanceService(db)
#     return balance_service.get_daily_balance(user_id, year, month, day)

@router.get("/stats/{user_id}", response_model=dict)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.get_user_stats(user_id)

@router.get("/streak/{user_id}", response_model=dict)
def get_user_streak(user_id: int, db: Session = Depends(get_db)):
    balance_service = BalanceService(db)
    return balance_service.get_user_streak(user_id)

@router.get("/weekly-score")
async def get_weekly_balance_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """지난 7일간의 평균 밸런스 점수를 반환합니다."""
    try:
        balance_service = BalanceService(db)
        weekly_score = balance_service.get_weekly_balance_score(int(str(current_user.id)))
        return {"weekly_balance_score": round(weekly_score, 1)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/days-since-joined")
async def get_days_since_joined(
    current_user: User = Depends(get_current_user)
) -> dict:
    """사용자의 가입 후 경과 일수를 반환합니다."""
    created_at = getattr(current_user, 'created_at', None)
    if not created_at:
        return {"days": 0}
    
    days = (datetime.now() - created_at).days
    return {"days": max(1, days)}  # 최소 1일로 표시 

@router.put("/user/calorie-goal")
async def update_calorie_goal(
    daily_calorie_goal: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 일일 칼로리 목표를 업데이트합니다."""
    try:
        setattr(current_user, 'daily_calorie_goal', daily_calorie_goal)
        db.commit()
        return {"message": "Updated successfully", "daily_calorie_goal": daily_calorie_goal}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 프로필 정보를 조회합니다."""
    return current_user

@router.put("/users/profile", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 프로필 정보를 업데이트합니다."""
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user 