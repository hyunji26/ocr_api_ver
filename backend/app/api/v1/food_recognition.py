# -*- coding: utf-8 -*-
from fastapi import APIRouter, UploadFile, File
import logging
from app.services.ocr.ocr_service import OCRService
from app.services.nutrition.nutrition_service import NutritionService
from app.schemas.food import FoodRecognitionResponse

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/food", tags=["Food Recognition"])

ocr_service = OCRService()
nutrition_service = NutritionService()

@router.post("/analyze")
async def analyze_food_image(file: UploadFile = File(...)):
    """
    음식 이미지를 분석하여 영양 정보를 반환합니다.
    1. OCR을 사용하여 이미지에서 음식 이름을 추출
    2. 추출된 음식 이름을 menu_dict와 유사도 검사하여 정제
    3. 정제된 음식 이름으로 영양 정보 조회 (중복 제거)
    """
    try:
        logger.info("=== API 호출 시작 ===")
        
        # 최소 신뢰도 임계값 설정
        MIN_OCR_CONFIDENCE = 0.2  # OCR 결과 신뢰도 최소값 (0.3 -> 0.2로 수정)
        MIN_MENU_SIMILARITY = 0.6  # 메뉴 유사도 최소값
        
        # 이미지에서 텍스트 추출
        contents = await file.read()
        logger.info("OCR 서비스 호출 시작")
        extracted_texts = await ocr_service.extract_text(contents)
        
        if not extracted_texts:
            return {"error": "텍스트를 찾을 수 없습니다."}
        
        # OCR 신뢰도가 낮은 결과 필터링
        extracted_texts = [
            text for text in extracted_texts 
            if text["confidence"] >= MIN_OCR_CONFIDENCE
        ]
        
        if not extracted_texts:
            return {"error": "신뢰도가 높은 텍스트를 찾을 수 없습니다."}
        
        # menu_dict에 있는 메뉴만 필터링
        filtered_texts = []
        for text_info in extracted_texts:
            menu, similarity = ocr_service.extract_menu_from_text_with_similarity(text_info["text"])
            if menu and similarity >= MIN_MENU_SIMILARITY:  # 메뉴 유사도가 기준값 이상인 경우만 추가
                filtered_texts.append({
                    "original_text": text_info["original_text"],
                    "text": menu,  # 정제된 메뉴 이름
                    "confidence": text_info["confidence"],
                    "menu_similarity": similarity  # 메뉴 유사도 추가
                })
        
        if not filtered_texts:
            logger.warning("메뉴 사전에서 찾을 수 있는 유사도 높은 음식이 없습니다.")
            return {
                "detected_texts": extracted_texts,
                "error": "메뉴 사전에서 찾을 수 있는 유사도 높은 음식이 없습니다."
            }
        
        # 중복 제거: 같은 메뉴는 가장 높은 유사도를 가진 것만 남김
        unique_foods = {}
        for text_info in filtered_texts:
            food_name = text_info["text"]
            score = text_info["confidence"] * 0.4 + text_info["menu_similarity"] * 0.6  # 가중 평균 점수
            
            if food_name not in unique_foods or score > unique_foods[food_name]["score"]:
                unique_foods[food_name] = {
                    "info": text_info,
                    "score": score
                }
        
        # 정제된 텍스트에 대해서만 영양 정보 조회
        found_foods = []
        logger.info("영양 정보 조회 시작")
        
        for food_data in unique_foods.values():
            text_info = food_data["info"]
            food_name = text_info["text"]
            confidence = text_info["confidence"]
            menu_similarity = text_info["menu_similarity"]
            
            # 영양 정보 조회
            nutrition_info = await nutrition_service.extract_nutrition_info(food_name, confidence)
            
            # 영양 정보가 있는 경우 결과에 추가
            if nutrition_info["calories"] != "N/A":
                found_foods.append({
                    "name": food_name,
                    "original_text": text_info["original_text"],
                    "confidence": confidence,
                    "menu_similarity": menu_similarity,
                    "nutrition_info": nutrition_info
                })
        
        # 음식을 찾지 못한 경우
        if not found_foods:
            logger.warning("영양 정보가 있는 음식을 찾지 못했습니다.")
            return {
                "detected_texts": extracted_texts,
                "filtered_texts": filtered_texts,
                "error": "영양 정보가 있는 음식을 찾지 못했습니다."
            }
        
        # 신뢰도와 유사도의 가중 평균으로 정렬
        found_foods.sort(key=lambda x: (x["confidence"] * 0.4 + x["menu_similarity"] * 0.6), reverse=True)
        
        result = {
            "detected_texts": extracted_texts,      # OCR로 추출된 모든 텍스트
            "filtered_texts": filtered_texts,       # menu_dict 기반으로 필터링된 텍스트
            "found_foods": found_foods,             # 영양 정보가 있는 모든 음식 목록 (중복 제거됨)
            "selected_food": found_foods[0]         # 가장 높은 점수의 음식을 대표로 선택
        }
        
        # 영양 정보가 있는 음식들만 로그로 출력
        logger.info("=== 영양 정보 찾은 음식 목록 (중복 제거됨) ===")
        for food in found_foods:
            logger.info(f"음식: {food['name']} (원본: {food['original_text']}, OCR 신뢰도: {food['confidence']:.2f}, 메뉴 유사도: {food['menu_similarity']:.2f})")
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