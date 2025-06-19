import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import food_recognition

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # 기존 로그 설정을 강제로 덮어씁니다
)

# 로거 가져오기
logger = logging.getLogger(__name__)

# 각 모듈의 로거 레벨 설정
logging.getLogger('app.api.v1.food_recognition').setLevel(logging.INFO)
logging.getLogger('app.services.ocr.ocr_service').setLevel(logging.INFO)
logging.getLogger('app.services.nutrition.nutrition_service').setLevel(logging.INFO)

app = FastAPI(title="Food Recognition API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 앱의 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(food_recognition.router, prefix="/api/v1")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"status": "Food Recognition API is running"}

@app.on_event("startup")
async def startup_event():
    logger.info("=== 서버 시작됨 ===")
    logger.info("CORS origins: http://localhost:3000")
    logger.info("API 엔드포인트: /api/v1/food/analyze")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== 서버 종료됨 ===")

# ASGI 애플리케이션을 main으로 export
main = app 