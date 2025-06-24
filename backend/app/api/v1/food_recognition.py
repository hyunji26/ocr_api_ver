# -*- coding: utf-8 -*-
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import logging
from app.services.ocr.ocr_service import OCRService
from app.services.nutrition.nutrition_service import NutritionService
from app.schemas.food import FoodRecognitionResponse
from difflib import get_close_matches
import re
from app.api.v1.balance import get_current_user
from typing import List, Dict, Any, Optional

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/food", tags=["Food Recognition"])

ocr_service = OCRService()
nutrition_service = NutritionService()

# OCR 신뢰도 임계값
HIGH_CONFIDENCE_THRESHOLD = 0.5  # 높은 신뢰도 기준
MIN_OCR_CONFIDENCE = 0.1        # 최소 신뢰도 기준

def _clean_and_normalize_text(text: str) -> str:
    """텍스트를 정제하고 정규화합니다."""
    if not text or not text.strip():
        return ""

    # 1. 기본 정리
    cleaned = text.strip()
    
    # 2. OCR 자주 틀리는 단어만 최소 교정
    ocr_errors = {
        "덜밥": "덮밥",
        "째개": "찌개",
        "찌게": "찌개",
        "김치째": "김치찌개",
        "부대째": "부대찌개",
        "비방": "비빔",
        "번밥": "빔밥",
        "덩밥": "덮밥",
        "멩이": "면",
        "회비": "회"
    }
    
    for error, correction in ocr_errors.items():
        cleaned = cleaned.replace(error, correction)
    
    # 3. 수식어 제거
    taste_modifiers = [
        r'\b매운\b', r'\b매움\b', r'\b매콤한\b', r'\b얼큰한\b',
        r'\b달콤한\b', r'\b달콩\b', r'\b달달한\b',
        r'\b특제\b', r'\b프리미엄\b', r'\b신메뉴\b', 
        r'\b베스트\b', r'\b인기\b', r'\b추천\b',
        r'\b특별\b', r'\b정성껏\b', r'\b장인의\b', 
        r'\b명품\b', r'\b정통\b', r'\b오리지널\b'
    ]
    
    for modifier in taste_modifiers:
        cleaned = re.sub(modifier, '', cleaned, flags=re.IGNORECASE)
    
    # 4. 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    # 5. 최소 길이 확인
    if len(cleaned) < 2:
        return text.strip()
    
    # 6. 메뉴 유사도 기반 자동 교정 시도
    corrected = ocr_service.correct_with_levenshtein(cleaned)
    return corrected if corrected else cleaned

@router.post("/analyze")
async def analyze_food_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    음식 이미지를 분석하여 영양 정보를 반환합니다.
    1. OCR을 사용하여 이미지에서 음식 이름을 추출
    2. 추출된 음식 이름을 정제,후처리
    3. 정제된 음식 이름으로 영양 정보 조회
    """
    try:
        logger.info("=== API 호출 시작 ===")
        
        # 이미지에서 텍스트 추출
        contents = await file.read()
        logger.info("OCR 서비스 호출 시작")
        extracted_texts = await ocr_service.extract_text(contents)
        
        if not extracted_texts:
            raise HTTPException(status_code=400, detail="텍스트를 찾을 수 없습니다.")
            
        # 모든 OCR 결과 로깅
        logger.info("=== 전체 OCR 결과 ===")
        for text in extracted_texts:
            logger.info(f"텍스트: {text['text']}, 신뢰도: {text['confidence']:.2f}, 좌표: {text.get('bbox', 'N/A')}")
        logger.info("=== OCR 결과 끝 ===")
        
        # OCR 신뢰도가 낮은 결과 필터링 (단, 메뉴 유사도가 높으면 예외 허용)
        filtered_by_confidence = []
        for text in extracted_texts:
            if text["confidence"] >= HIGH_CONFIDENCE_THRESHOLD:
                filtered_by_confidence.append(text)
                logger.info(f"높은 신뢰도로 포함: {text['text']} (신뢰도: {text['confidence']:.2f})")
            else:
                # 신뢰도가 낮아도 메뉴 유사도를 먼저 확인
                if text["confidence"] >= MIN_OCR_CONFIDENCE:  # 최소 신뢰도 이상
                    filtered_by_confidence.append(text)
                    logger.info(f"낮은 신뢰도({text['confidence']:.2f})이지만 포함: {text['text']}")
                else:
                    logger.info(f"매우 낮은 신뢰도로 제외: {text['text']} (신뢰도: {text['confidence']:.2f})")
        
        if not filtered_by_confidence:
            raise HTTPException(status_code=400, detail="신뢰도가 높은 텍스트를 찾을 수 없습니다.")
        
        # 영양 정보 조회
        logger.info("영양 정보 조회 시작")
        nutrition_info_list = []
        seen_texts = set()  # 중복 제거를 위한 집합
        
        for text_info in filtered_by_confidence:
            text = text_info["text"]
            if text not in seen_texts:  # 중복 제거
                seen_texts.add(text)
                nutrition_info = await nutrition_service.extract_nutrition_info(text, text_info["confidence"])
                if nutrition_info:
                    nutrition_info_list.append(nutrition_info)
        
        if not nutrition_info_list:
            raise HTTPException(status_code=400, detail="영양 정보를 찾을 수 없습니다.")
        
        # 영양 정보를 찾은 음식 목록 로깅
        logger.info("=== 영양 정보 찾은 음식 목록 (중복 제거됨) ===")
        for text_info in filtered_by_confidence:
            logger.info(f"음식: {text_info['text']} (원본: {text_info['text']}, OCR 신뢰도: {text_info['confidence']:.2f})")
            logger.info("---")
        
        logger.info("=== API 호출 완료 ===")
        return nutrition_info_list
        
    except Exception as e:
        logger.error(f"API 호출 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 