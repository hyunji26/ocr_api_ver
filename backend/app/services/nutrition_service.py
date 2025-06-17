import aiohttp
from app.schemas.food import FoodRecognitionResponse, NutrientInfo
import logging

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        # 실제 프로덕션에서는 환경 변수로 관리해야 합니다
        self.api_base_url = "https://api.example.com/v1/nutrition"  # 실제 사용할 API URL로 변경 필요
        self.api_key = "your_api_key_here"  # 실제 API 키로 변경 필요

    async def analyze_food_info(self, text: str) -> FoodRecognitionResponse:
        """
        텍스트에서 음식 이름을 추출하고 외부 API를 통해 영양 정보를 가져옵니다.
        """
        # 기본 응답 구조
        food_info = {
            "name": text.strip(),  # OCR로 추출된 텍스트를 음식 이름으로 사용
            "calories": 0,
            "nutrients": {
                "carbs": NutrientInfo(amount=0, unit="g", daily_value=46),
                "protein": NutrientInfo(amount=0, unit="g", daily_value=37),
                "fat": NutrientInfo(amount=0, unit="g", daily_value=16),
                "fiber": NutrientInfo(amount=0, unit="g", daily_value=5)
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/search",
                    params={"query": text.strip()},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # API 응답을 우리의 형식에 맞게 변환
                        # 실제 API의 응답 구조에 따라 이 부분을 수정해야 합니다
                        if data.get("items"):
                            item = data["items"][0]  # 첫 번째 결과 사용
                            food_info.update({
                                "calories": item.get("calories", 0),
                                "nutrients": {
                                    "carbs": NutrientInfo(
                                        amount=item.get("carbohydrates", 0),
                                        unit="g",
                                        daily_value=46
                                    ),
                                    "protein": NutrientInfo(
                                        amount=item.get("protein", 0),
                                        unit="g",
                                        daily_value=37
                                    ),
                                    "fat": NutrientInfo(
                                        amount=item.get("fat", 0),
                                        unit="g",
                                        daily_value=16
                                    ),
                                    "fiber": NutrientInfo(
                                        amount=item.get("fiber", 0),
                                        unit="g",
                                        daily_value=5
                                    )
                                }
                            })
                            logger.info(f"영양 정보 조회 성공: {text}")
                    else:
                        logger.error(f"API 요청 실패: {response.status}")

        except Exception as e:
            logger.error(f"영양 정보 조회 중 오류 발생: {str(e)}")

        return FoodRecognitionResponse(**food_info) 