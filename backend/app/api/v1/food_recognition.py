from fastapi import APIRouter, UploadFile, File
import logging
from app.services.ocr.ocr_service import OCRService
from app.services.nutrition.nutrition_service import NutritionService
from app.schemas.food import FoodRecognitionResponse

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/food", tags=["Food Recognition"])

ocr_service = OCRService()
nutrition_service = NutritionService()

@router.post("/analyze")
async def analyze_food_image(file: UploadFile = File(...)):
    """
    음식 이미지를 분석하여 영양 정보를 반환합니다.
    """
    try:
        logger.info("=== API 호출 시작 ===")
        logger.info(f"이미지 분석 시작 - 파일명: {file.filename}")
        logger.info(f"파일 타입: {file.content_type}")
        
        # 이미지에서 텍스트 추출
        contents = await file.read()
        logger.info(f"이미지 크기: {len(contents)} bytes")
        
        logger.info("OCR 서비스 호출 시작")
        text = await ocr_service.extract_text(contents)
        logger.info(f"추출된 텍스트: {text}")
        
        # 텍스트에서 영양 정보 추출
        logger.info("영양 정보 추출 시작")
        nutrition_info = await nutrition_service.extract_nutrition_info(text)
        logger.info(f"추출된 영양 정보: {nutrition_info}")
        
        result = {
            "calories": nutrition_info.get("calories", "N/A"),
            "nutrients": nutrition_info.get("nutrients", []),
            "text": text  # 디버깅용
        }
        logger.info(f"최종 결과: {result}")
        logger.info("=== API 호출 완료 ===")
        
        return result
    except Exception as e:
        logger.error(f"=== 에러 발생 ===")
        logger.error(f"에러 타입: {type(e)}")
        logger.error(f"에러 메시지: {str(e)}")
        return {"error": str(e)} 