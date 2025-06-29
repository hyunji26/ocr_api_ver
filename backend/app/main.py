import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import food_recognition, balance
from app.database import engine, Base, create_tables
from sqlalchemy import inspect
from app.models.balance import User, Meal
import pytz
from datetime import datetime

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 각 모듈의 로거 레벨 설정
logging.getLogger('app.api.v1.food_recognition').setLevel(logging.INFO)
logging.getLogger('app.services.ocr.ocr_service').setLevel(logging.INFO)
logging.getLogger('app.services.nutrition.nutrition_service').setLevel(logging.INFO)
logging.getLogger('app.api.v1.balance').setLevel(logging.INFO)

app = FastAPI(title="Food Recognition API")

# CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    logger.info(f"Request headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# API 라우터 등록
app.include_router(food_recognition.router, prefix="/api/v1")
app.include_router(balance.router, prefix="/api/v1")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"status": "Food Recognition API is running"}

@app.on_event("startup")
async def startup_event():
    logger.info("=== 서버 시작됨 ===")
    
    try:
        # 테이블 강제 생성
        logger.info("데이터베이스 테이블을 생성합니다.")
        create_tables() 
        logger.info("테이블 생성 완료")
    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {str(e)}")
    
    logger.info("CORS origins: http://localhost:3000")
    logger.info("API 엔드포인트: /api/v1/food/analyze")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== 서버 종료됨 ===")

# ASGI 애플리케이션을 main으로 export
main = app 