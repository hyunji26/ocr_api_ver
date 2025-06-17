from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import food_recognition

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
    return {"status": "Food Recognition API is running"} 