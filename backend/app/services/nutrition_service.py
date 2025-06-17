import re
from app.schemas.food import FoodRecognitionResponse, NutrientInfo

class NutritionService:
    async def analyze_food_info(self, text: str) -> FoodRecognitionResponse:
        """
        추출된 텍스트에서 음식 정보를 분석하여 구조화된 데이터로 반환
        """
        # 기본값 설정
        food_info = {
            "name": "",
            "calories": 0,
            "nutrients": {
                "carbs": NutrientInfo(amount=0, unit="g", daily_value=46),
                "protein": NutrientInfo(amount=0, unit="g", daily_value=37),
                "fat": NutrientInfo(amount=0, unit="g", daily_value=16),
                "fiber": NutrientInfo(amount=0, unit="g", daily_value=5)
            }
        }
        
        # 메뉴명 추출
        menu_match = re.search(r'메뉴:\s*([가-힣\s]+)', text)
        if menu_match:
            food_info["name"] = menu_match.group(1).strip()
            
        # 칼로리 추출
        calories_match = re.search(r'(\d+)\s*kcal', text)
        if calories_match:
            food_info["calories"] = int(calories_match.group(1))
            
        # 영양소 정보 추출
        nutrient_matches = {
            "탄수화물": "carbs",
            "단백질": "protein",
            "지방": "fat",
            "섬유질": "fiber"
        }
        
        for kr_name, eng_name in nutrient_matches.items():
            match = re.search(f'{kr_name}[\\s:]*([\d.]+)g?', text)
            if match:
                amount = float(match.group(1))
                food_info["nutrients"][eng_name] = NutrientInfo(
                    amount=amount,
                    unit="g",
                    daily_value=food_info["nutrients"][eng_name].daily_value
                )
        
        return FoodRecognitionResponse(**food_info) 