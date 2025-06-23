import os
import re
import logging
import aiohttp
import ssl
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        logger.info("영양 정보 서비스 초기화")
        # API 키는 이미 인코딩되어 있으므로 그대로 사용
        self.api_key = 'DikYPQYEtB2A%2BwML43XYgXpRPMp06zngL5Yq5P8VlVfFKY9g46988MjMoeyrex0s876GbTbBGWDZzJQPT5aCEg%3D%3D'
        # 공식 문서의 엔드포인트 URL
        self.base_url = "http://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"
        
        logger.info(f"API 키 설정 확인: {self.api_key[:10]}... (길이: {len(self.api_key)})")
        logger.info(f"Base URL: {self.base_url}")

    async def _search_food(self, food_name: str) -> Optional[Dict]:
        """식약처 API를 통해 식품 영양정보를 검색합니다."""
        try:
            # API 키가 비어있는지 확인
            if not self.api_key:
                logger.error("API 키가 설정되지 않았습니다!")
                return None
                
            params = {
                'serviceKey': self.api_key,  # 이미 인코딩된 API 키 사용
                'FOOD_NM_KR': food_name,  # desc_kor 대신 FOOD_NM_KR 사용
                'pageNo': '1',
                'numOfRows': '1',
                'type': 'json'
            }
            
            async with aiohttp.ClientSession() as session:
                # URL에 직접 API 키를 포함시켜 호출
                url = f"{self.base_url}?serviceKey={self.api_key}"
                for key, value in params.items():
                    if key != 'serviceKey':  # API 키는 이미 포함됨
                        url += f"&{key}={value}"
                        
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 실제 API 응답 구조에 맞게 수정
                        items = data.get('body', {}).get('items', [])
                        
                        # items가 리스트이고 항목이 있는 경우 첫 번째 항목 사용
                        if isinstance(items, list) and items:
                            found_item = items[0]
                            logger.info(f"찾은 음식: {found_item.get('FOOD_NM_KR', '알 수 없음')}")
                            return found_item
                        else:
                            logger.warning(f"유효한 items를 찾을 수 없음: {items}")
                            return None
                    else:
                        logger.error(f"API 호출 실패: {response.status}")
                        response_text = await response.text()
                        logger.error(f"응답 내용: {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"식약처 API 호출 중 오류 발생: {str(e)}")
            return None

    def _clean_food_name(self, food_name: str) -> str:
        """검색을 위해 음식 이름을 정제합니다."""
        # 특수문자 및 공백 처리
        cleaned = re.sub(r'[^\w\s가-힣]', ' ', food_name)
        
        # 수식어 제거
        modifiers = [
            "수제", "마약", "특제", "프리미엄", "신메뉴", "NEW", "베스트", "인기", "추천",
            "매운", "매움", "특별", "정성껏", "장인의", "명품", "정통", "오리지널"
        ]
        for modifier in modifiers:
            cleaned = cleaned.replace(modifier, "")
        
        # OCR 오류 수정
        ocr_errors = {
            "치키가라아게": "치킨가라아게",
            "째개": "찌개",
            "찌게": "찌개"
        }
        for error, correction in ocr_errors.items():
            cleaned = cleaned.replace(error, correction)
        
        # 여러 공백을 하나의 공백으로
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    async def extract_nutrition_info(self, food_name: str, confidence: float = 1.0) -> Dict:
        """
        음식 이름으로 영양 정보를 검색합니다.
        
        Args:
            food_name (str): OCR로 추출한 음식 이름
            confidence (float): OCR 신뢰도 점수
            
        Returns:
            Dict: 영양 정보 (칼로리, 탄수화물, 단백질, 지방)
        """
        try:
            # 음식 이름 정제
            cleaned_name = self._clean_food_name(food_name)
            logger.info(f"정제된 음식 이름: {cleaned_name} (원본: {food_name})")
            
            # 식약처 API로 검색
            result = await self._search_food(cleaned_name)
            
            if not result:
                # 정제된 이름으로 검색 실패시 원본 이름으로 재시도
                result = await self._search_food(food_name)
            
            if result:
                nutrition_info = {
                    "name": result.get('FOOD_NM_KR', 'N/A'),  # 식품명 추가
                    "calories": float(result.get('AMT_NUM1', 0)),  # 열량 (kcal)
                    "nutrients": {
                        "carbohydrates": float(result.get('AMT_NUM6', 0)),  # 탄수화물 (g)
                        "protein": float(result.get('AMT_NUM3', 0)),  # 단백질 (g)
                        "fat": float(result.get('AMT_NUM4', 0))  # 지방 (g)
                    }
                }
                logger.info(f"'{food_name}'의 영양 정보 찾음: {nutrition_info}")
                return nutrition_info
            
            logger.warning(f"'{food_name}'에 대한 영양 정보를 찾을 수 없음")
            return self.get_empty_nutrition()
            
        except Exception as e:
            logger.error(f"영양 정보 추출 중 오류 발생: {str(e)}")
            return self.get_empty_nutrition()

    def get_empty_nutrition(self) -> Dict:
        """빈 영양 정보를 반환합니다."""
        return {
            "name": "N/A",  # 식품명 필드 추가
            "calories": 0,
            "nutrients": {
                "carbohydrates": 0,
                "protein": 0,
                "fat": 0
            }
        }