import os
import re
import logging
import aiohttp
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        logger.info("영양 정보 서비스 초기화")
        self.api_key = os.getenv('DikYPQYEtB2A%2BwML43XYgXpRPMp06zngL5Yq5P8VlVfFKY9g46988MjMoeyrex0s876GbTbBGWDZzJQPT5aCEg%3D%3D', '')
        self.base_url = "http://openapi.foodsafetykorea.go.kr/api"
        self.service_id = "I2790"  # 식품영양성분 API 서비스 ID

    async def _search_food(self, food_name: str) -> Optional[Dict]:
        """식약처 API를 통해 식품 영양정보를 검색합니다."""
        try:
            params = {
                'keyId': self.api_key,
                'serviceId': self.service_id,
                'desc_kor': food_name,
                'pageNo': '1',
                'numOfRows': '1',
                'type': 'json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/{self.service_id}/json", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # API 응답 확인
                        result = data.get(self.service_id, {}).get('row', [])
                        if result:
                            return result[0]
                    return None
                    
        except Exception as e:
            logger.error(f"식약처 API 호출 중 오류 발생: {str(e)}")
            return None

    def _clean_food_name(self, food_name: str) -> str:
        """검색을 위해 음식 이름을 정제합니다."""
        # 특수문자 및 공백 처리
        cleaned = re.sub(r'[^\w\s가-힣]', ' ', food_name)
        # 불필요한 수식어 제거
        modifiers = ['매운', '매움', '특제', '프리미엄', '마약', '특별']
        for modifier in modifiers:
            cleaned = cleaned.replace(modifier, '')
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
                    "calories": str(result.get('NUTR_CONT1', 'N/A')),  # 열량
                    "nutrients": {
                        "carbohydrates": str(result.get('NUTR_CONT2', 'N/A')),  # 탄수화물
                        "protein": str(result.get('NUTR_CONT3', 'N/A')),  # 단백질
                        "fat": str(result.get('NUTR_CONT4', 'N/A'))  # 지방
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
            "calories": "N/A",
            "nutrients": {
                "carbohydrates": "N/A",
                "protein": "N/A",
                "fat": "N/A"
            }
        } 