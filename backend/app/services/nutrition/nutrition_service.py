import re
import logging
import pandas as pd
import os
from typing import Dict, List, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        logger.info("영양 정보 서비스 초기화")
        self.nutrition_data = None
        self.MIN_SIMILARITY = 0.6  # 최소 유사도 threshold
        self.load_nutrition_data()

    def load_nutrition_data(self):
        """CSV 파일에서 영양 정보를 로드합니다."""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), "data", "nutrition_db.csv")
            # CSV 파일 읽기 (한글 인코딩 처리)
            self.nutrition_data = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # 음식 이름 컬럼을 소문자로 변환하여 검색을 용이하게 합니다
            if '식품명' in self.nutrition_data.columns:
                self.nutrition_data['식품명_lower'] = self.nutrition_data['식품명'].str.lower()
        except Exception as e:
            logger.error(f"CSV 파일 로드 중 오류 발생: {str(e)}")
            raise e

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """두 문자열 간의 유사도를 계산합니다."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def find_most_similar_food(self, food_name: str) -> Optional[str]:
        """가장 유사한 음식 이름을 찾습니다."""
        best_similarity = 0
        best_match = None

        for db_food in self.nutrition_data['식품명'].values:
            similarity = self.calculate_similarity(food_name, db_food)
            if similarity > best_similarity and similarity >= self.MIN_SIMILARITY:
                best_similarity = similarity
                best_match = db_food

        if best_match:
            logger.info(f"'{food_name}'와(과) 가장 유사한 음식: '{best_match}' (유사도: {best_similarity:.2f})")
        
        return best_match

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
            # 검색을 위해 소문자로 변환
            food_name_lower = food_name.lower()
            
            # 정확한 일치 검색
            result = self.nutrition_data[self.nutrition_data['식품명_lower'] == food_name_lower]
            
            # 정확한 일치가 없는 경우, 유사도 검사
            if result.empty:
                similar_food = self.find_most_similar_food(food_name)
                if similar_food:
                    result = self.nutrition_data[self.nutrition_data['식품명'] == similar_food]
            
            if result.empty:
                logger.info(f"'{food_name}'에 대한 영양 정보를 찾을 수 없음")
                return self.get_empty_nutrition()
            
            # 첫 번째 결과 반환
            first_result = result.iloc[0]
            nutrition_info = {
                "calories": str(first_result['에너지(kcal)']),
                "nutrients": {
                    "carbohydrates": str(first_result['탄수화물(g)']),
                    "protein": str(first_result['단백질(g)']),
                    "fat": str(first_result['지방(g)'])
                }
            }
            logger.info(f"'{food_name}'의 영양 정보 찾음: {nutrition_info}")
            return nutrition_info
            
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