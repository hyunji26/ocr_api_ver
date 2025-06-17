import re
import logging

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        logger.info("영양 정보 서비스 초기화")
        # 칼로리와 영양소를 찾기 위한 정규표현식 패턴
        self.calorie_pattern = r'(\d+)\s*kcal'
        self.nutrient_patterns = {
            '탄수화물': r'탄수화물\s*(\d+\.?\d*)\s*g',
            '단백질': r'단백질\s*(\d+\.?\d*)\s*g',
            '지방': r'지방\s*(\d+\.?\d*)\s*g',
            '나트륨': r'나트륨\s*(\d+\.?\d*)\s*mg'
        }
        logger.info("영양 정보 패턴 설정 완료")

    async def extract_nutrition_info(self, text: str) -> dict:
        """
        텍스트에서 영양 정보를 추출합니다.
        """
        try:
            logger.info(f"영양 정보 추출 시작 - 입력 텍스트: {text}")

            # 칼로리 추출
            calorie_match = re.search(self.calorie_pattern, text)
            calories = calorie_match.group(1) if calorie_match else "N/A"
            logger.info(f"추출된 칼로리: {calories}")

            # 영양소 추출
            nutrients = {}
            for nutrient, pattern in self.nutrient_patterns.items():
                match = re.search(pattern, text)
                if match:
                    nutrients[nutrient] = f"{match.group(1)}g"
                    logger.info(f"추출된 영양소 - {nutrient}: {match.group(1)}g")
                else:
                    logger.info(f"{nutrient} 정보를 찾을 수 없음")

            result = {
                "calories": calories,
                "nutrients": nutrients
            }
            logger.info(f"영양 정보 추출 완료: {result}")
            return result

        except Exception as e:
            logger.error(f"영양 정보 추출 중 오류 발생: {str(e)}")
            raise Exception(f"영양 정보 추출 중 오류 발생: {str(e)}") 