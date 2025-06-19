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

def _clean_and_normalize_text(text: str) -> str:
    """텍스트를 정제하고 정규화합니다."""
    if not text or not text.strip():
        return ""
    
    # 1. 기본 정리
    cleaned = text.strip()
    
    # 2. OCR 오류 수정 (먼저 수행) - 확장된 버전
    ocr_errors = {
        "치키가라아게": "치킨가라아게",
        "째개": "찌개",
        "찌게": "찌개",
        "덜밥": "덮밥",
        "방밥": "빔밥",
        "비방": "비빔",
        # 한글 자모 혼동 오류 추가
        "번": "빔",      # 비빔밥 -> 비번밥 오류
        "덩": "덮",      # 덮밥 -> 덩밥 오류
        "멩": "면",      # 라면 -> 라멩 오류
        "방": "빔",      # 비빔 -> 비방 오류
        "골": "콜",      # 콜라 -> 골라 오류
        "멩이": "면",    # 라면 -> 라멩이 오류
        "번밥": "빔밥",  # 비빔밥 -> 비번밥 오류
        "덩밥": "덮밥",  # 덮밥 -> 덩밥 오류
        "회비": "회",    # 육회 -> 육회비 오류
        "비번": "비빔",  # 비빔 -> 비번 오류
        # 복합 단어 보존
        "면사리": "면사리",
        "라면": "라면",
        "사리": "사리",
    }
    
    for error, correction in ocr_errors.items():
        cleaned = cleaned.replace(error, correction)
    
    # 3. 복합 음식명 특별 처리
    # "육회비빔밥" 같은 복합 음식명 처리
    if "육회" in cleaned and "빔밥" in cleaned:
        cleaned = "육회비빔밥"
    elif "육회" in cleaned and "덮밥" in cleaned:
        cleaned = "육회덮밥"
    elif "라면" in cleaned and "사리" in cleaned:
        cleaned = "라면사리"
    
    # 4. 수식어 제거 (더 정교하게)
    # 단어 경계를 고려한 수식어 제거
    import re
    
    # 브랜드/크기 관련 수식어 (단어 경계 고려)
    brand_modifiers = [
        r'\bGrande\b', r'\bVenti\b', r'\bTall\b', r'\bRegular\b', 
        r'\bLarge\b', r'\bMedium\b', r'\bSmall\b', r'\bNEW\b'
    ]
    
    # 맛/특성 관련 수식어 (단어 경계 고려)
    taste_modifiers = [
        r'\b매운\b', r'\b매움\b', r'\b특제\b', r'\b프리미엄\b', 
        r'\b신메뉴\b', r'\b베스트\b', r'\b인기\b', r'\b추천\b',
        r'\b특별\b', r'\b정성껏\b', r'\b장인의\b', r'\b명품\b', 
        r'\b정통\b', r'\b오리지널\b'
    ]
    
    # 색상 관련 수식어 (단어 경계 고려)
    color_modifiers = [
        r'\b그린\b', r'\b레드\b', r'\b블루\b', r'\b옐로우\b'
    ]
    
    # 모든 수식어 제거
    all_modifiers = brand_modifiers + taste_modifiers + color_modifiers
    for modifier in all_modifiers:
        cleaned = re.sub(modifier, '', cleaned, flags=re.IGNORECASE)
    
    # 5. 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    # 6. 최소 길이 확인 (너무 짧으면 원본 반환)
    if len(cleaned) < 2:
        return text.strip()
    
    return cleaned

@router.post("/analyze")
async def analyze_food_image(file: UploadFile = File(...)):
    """
    음식 이미지를 분석하여 영양 정보를 반환합니다.
    1. OCR을 사용하여 이미지에서 음식 이름을 추출
    2. 추출된 음식 이름을 정제,후처리리
    3. 정제된 음식 이름으로 영양 정보 조회 (중복 제거)
    """
    try:
        logger.info("=== API 호출 시작 ===")
        
        # 최소 신뢰도 임계값 설정
        MIN_OCR_CONFIDENCE = 0.15  # OCR 결과 신뢰도 최소값 (0.3 -> 0.15로 낮춤)
        
        # 이미지에서 텍스트 추출
        contents = await file.read()
        logger.info("OCR 서비스 호출 시작")
        extracted_texts = await ocr_service.extract_text(contents)
        
        if not extracted_texts:
            return {"error": "텍스트를 찾을 수 없습니다."}
        
        # OCR 신뢰도가 낮은 결과 필터링 (단, 메뉴 유사도가 높으면 예외 허용)
        filtered_by_confidence = []
        for text in extracted_texts:
            if text["confidence"] >= MIN_OCR_CONFIDENCE:
                filtered_by_confidence.append(text)
            else:
                # 신뢰도가 낮아도 메뉴 유사도를 먼저 확인 (단, 너무 낮으면 제외)
                if text["confidence"] >= 0.1:  # 최소 10% 이상은 되어야 함 (0.2 -> 0.1로 낮춤)
                    result = ocr_service.extract_menu_from_text_with_similarity(text["text"])
                    if result is not None:
                        menu, similarity = result
                        if similarity >= 0.7:  # 메뉴 유사도가 70% 이상이면 포함 (0.8 -> 0.7로 낮춤)
                            logger.info(f"신뢰도 낮음({text['confidence']:.2f})이지만 메뉴 유사도 높음({similarity:.2f})으로 포함: {text['text']}")
                            filtered_by_confidence.append(text)
        
        if not filtered_by_confidence:
            return {"error": "신뢰도가 높은 텍스트를 찾을 수 없습니다."}
        
        # 텍스트 후처리 및 정제 (CSV 메뉴 사전 필터링 제거)
        processed_texts = []
        for text_info in filtered_by_confidence:
            # 텍스트 정제 (수식어 제거, OCR 오류 수정 등)
            cleaned_text = _clean_and_normalize_text(text_info["text"])
            if cleaned_text:
                processed_texts.append({
                    "original_text": text_info["original_text"],
                    "text": cleaned_text,  # 정제된 텍스트
                    "confidence": text_info["confidence"]
                })
        
        if not processed_texts:
            return {"error": "정제된 텍스트를 찾을 수 없습니다."}
        
        # 중복 제거: 같은 정제된 텍스트는 가장 높은 신뢰도를 가진 것만 남김
        unique_foods = {}
        for text_info in processed_texts:
            food_name = text_info["text"]
            confidence = text_info["confidence"]
            
            if food_name not in unique_foods or confidence > unique_foods[food_name]["confidence"]:
                unique_foods[food_name] = text_info
        
        # 정제된 텍스트로 영양 정보 조회
        found_foods = []
        logger.info("영양 정보 조회 시작")
        
        for food_name, text_info in unique_foods.items():
            confidence = text_info["confidence"]
            
            # 영양 정보 조회
            nutrition_info = await nutrition_service.extract_nutrition_info(food_name, confidence)
            
            # 영양 정보가 있는 경우 결과에 추가
            if nutrition_info["calories"] != "N/A":
                found_foods.append({
                    "name": food_name,
                    "original_text": text_info["original_text"],
                    "confidence": confidence,
                    "nutrition_info": nutrition_info
                })
        
        # 음식을 찾지 못한 경우
        if not found_foods:
            logger.warning("영양 정보가 있는 음식을 찾지 못했습니다.")
            return {
                "detected_texts": extracted_texts,
                "processed_texts": processed_texts,
                "error": "영양 정보가 있는 음식을 찾지 못했습니다."
            }
        
        # 신뢰도로 정렬
        found_foods.sort(key=lambda x: x["confidence"], reverse=True)
        
        result = {
            "detected_texts": extracted_texts,      # OCR로 추출된 모든 텍스트
            "processed_texts": processed_texts,     # 후처리 및 정제된 텍스트
            "found_foods": found_foods,             # 영양 정보가 있는 모든 음식 목록 (중복 제거됨)
            "selected_food": found_foods[0]         # 가장 높은 신뢰도의 음식을 대표로 선택
        }
        
        # 영양 정보가 있는 음식들만 로그로 출력
        logger.info("=== 영양 정보 찾은 음식 목록 (중복 제거됨) ===")
        for food in found_foods:
            logger.info(f"음식: {food['name']} (원본: {food['original_text']}, OCR 신뢰도: {food['confidence']:.2f})")
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