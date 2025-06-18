# -*- coding: utf-8 -*-
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
    1. OCR을 사용하여 이미지에서 음식 이름을 추출
    2. 추출된 음식 이름으로 엑셀 DB에서 영양 정보 조회
    """
    try:
        logger.info("=== API 호출 시작 ===")
        
        # 이미지에서 텍스트 추출
        contents = await file.read()
        logger.info("OCR 서비스 호출 시작")
        extracted_texts = await ocr_service.extract_text(contents)
        
        if not extracted_texts:
            return {"error": "텍스트를 찾을 수 없습니다."}
        
        # 각 추출된 텍스트에 대해 영양 정보 조회를 시도
        found_foods = []
        
        logger.info("영양 정보 조회 시작")
        for text_info in extracted_texts:
            food_name = text_info["text"]
            confidence = text_info["confidence"]
            
            # 영양 정보 조회
            nutrition_info = await nutrition_service.extract_nutrition_info(food_name, confidence)
            
            # 영양 정보가 있는 경우 결과에 추가
            if nutrition_info["calories"] != "N/A":
                found_foods.append({
                    "name": food_name,
                    "confidence": confidence,
                    "nutrition_info": nutrition_info
                })
        
        # 음식을 찾지 못한 경우
        if not found_foods:
            logger.warning("영양 정보가 있는 음식을 찾지 못했습니다.")
            return {
                "detected_texts": extracted_texts,
                "error": "영양 정보가 있는 음식을 찾지 못했습니다."
            }
        
        # 신뢰도 기준으로 정렬
        found_foods.sort(key=lambda x: x["confidence"], reverse=True)
        
        result = {
            "detected_texts": extracted_texts,
            "found_foods": found_foods,  # 영양 정보가 있는 모든 음식 목록
            "selected_food": found_foods[0]  # 가장 신뢰도가 높은 음식을 대표로 선택
        }
        
        # 영양 정보가 있는 음식들만 로그로 출력
        logger.info("=== 영양 정보 찾은 음식 목록 ===")
        for food in found_foods:
            logger.info(f"음식: {food['name']} (신뢰도: {food['confidence']:.2f})")
            logger.info(f"  - 칼로리: {food['nutrition_info']['calories']}kcal")
            logger.info(f"  - 탄수화물: {food['nutrition_info']['nutrients']['carbohydrates']}g")
            logger.info(f"  - 단백질: {food['nutrition_info']['nutrients']['protein']}g")
            logger.info(f"  - 지방: {food['nutrition_info']['nutrients']['fat']}g")
            logger.info("---")
        
        logger.info("=== API 호출 완료 ===")
        
        return result
    except Exception as e:
        logger.error(f"=== 에러 발생 ===")
        logger.error(f"에러 타입: {type(e)}")
        logger.error(f"에러 메시지: {str(e)}")
        return {"error": str(e)} 