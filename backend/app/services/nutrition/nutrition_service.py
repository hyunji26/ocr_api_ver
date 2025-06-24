import os
import re
import logging
import aiohttp
import ssl
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        """영양 정보 서비스 초기화"""
        try:
            # CSV 파일 경로
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, 'data', 'nutrition_db.csv')
            
            # CSV 파일 읽기
            self.nutrition_db = pd.read_csv(csv_path)
            logger.info(f"영양 정보 DB 로드 완료: {len(self.nutrition_db)} 개의 메뉴")
            
        except Exception as e:
            logger.error(f"영양 정보 DB 로드 중 오류 발생: {str(e)}")
            self.nutrition_db = pd.DataFrame()  # 빈 DataFrame으로 초기화

        # 1인분 기준량 정의
        self.serving_size_guess = {
            "육회비빔밥": 500,
            "비빔밥": 450,
            "불고기덮밥": 400,
            "김치찌개": 350,
            "된장찌개": 350,
            "순두부찌개": 400,
            "부대찌개": 500,
            "삼겹살": 200,
            "갈비찜": 250,
            "닭갈비": 350,
            "제육볶음": 300,
            "치킨": 250,
            "튀김류": 150,
            "떡볶이": 400,
            "순대": 250,
            "김밥": 200,
            "라면": 500,
            "볶음밥": 400,
            "오므라이스": 450,
            "카레라이스": 450,
            "계란말이": 150,
            "계란후라이": 60,
            "스크램블에그": 100,
            "샐러드": 150,
            "우유": 200,
            "두유": 190,
            "요거트": 100,
            "바나나": 100,
            "사과": 200,
            "오렌지": 150,
            "밥": 210,
            "잡곡밥": 210,
            "현미밥": 210,
            "흰죽": 250,
            "죽": 300,
            "우동": 500,
            "잔치국수": 450,
            "칼국수": 500,
            "짬뽕": 550,
            "짜장면": 550,
            "돈까스": 300,
            "햄버거": 250,
            "피자": 130,
            "제육덮밥": 400,
            "오징어볶음": 300,
            "돼지김치찌개": 400,
            "참치순두부찌개": 400,
            "골뱅이비빔면": 450,
            "물냉면": 550,
            "비빔냉면": 500,
            "된장라면": 500,
            "공기밥": 210
        }

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
        # 원본 텍스트 보존
        original = food_name
        
        # 특수문자 및 공백 처리 (괄호는 유지)
        cleaned = food_name.strip()
        
        # 수량 정보 제거 (예: "2인분", "2인이상" 등)
        cleaned = re.sub(r'\s*\d+인(?:분|이상|)?\s*', '', cleaned)
        
        # 메뉴 단어 병합 패턴
        merge_patterns = {
            r'냉\s+면': '냉면',
            r'비빔\s+냉면': '비빔냉면',
            r'물\s+냉면': '물냉면',
            r'공\s+기\s+밥': '공기밥',
            r'김치\s+찌개': '김치찌개',
            r'된장\s+찌개': '된장찌개',
            r'순두부\s+찌개': '순두부찌개',
            r'부대\s+찌개': '부대찌개'
        }
        
        # 메뉴 단어 병합
        for pattern, replacement in merge_patterns.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # 불필요한 텍스트만 제거 (괄호는 유지)
        remove_texts = [
            '공기밥별도',
            '밥별도',
            '추가',
            '선택',
            '포장'
        ]
        
        # 불필요한 텍스트 제거 (괄호 내부 텍스트만)
        for text in remove_texts:
            # 괄호 안의 텍스트 제거
            cleaned = re.sub(f'\\({text}\\)', '()', cleaned)
            # 일반 텍스트 제거
            cleaned = re.sub(f'\\s*{text}\\s*', '', cleaned)
        
        # 빈 괄호 제거
        cleaned = re.sub(r'\(\s*\)', '', cleaned)
        
        # 메뉴 수식어 패턴
        modifiers = [
            "매름한", "매운", "달콤한", "달콤", "얼큰한", "얼큰", "맵고", "맛있는",
            "고소한", "신선한", "따뜻한", "따듯한", "차가운", "시원한", "짭짤한",
            "진한", "깔끔한", "풍미가득", "향긋한", "담백한", "부드러운",
            "특제", "특별한", "새로운", "인기", "최고", "추천", "모듬", "정통",
            "정성껏", "프리미엄", "수제", "장인의", "명품", "오리지널",
            "즉석", "직화", "바로", "얼른한", "촉촉한", "쫄깃한", "담백한",
            "깔끔한", "가성비", "고퀄리티", "재방문", "베스트"
        ]
        
        # 수식어 제거
        for modifier in modifiers:
            cleaned = re.sub(f'{modifier}\s*', '', cleaned)
        
        # OCR 오류 수정
        ocr_errors = {
            "치키가라아게": "치킨가라아게",
            "째개": "찌개",
            "찌게": "찌개",
            "비범": "비빔",
            "뷰음": "볶음",
            "뒷밥": "덮밥",
            "육회비범밥": "육회비빔밥",
            "제육뒷밥": "제육덮밥",
            "오징어뷰음": "오징어볶음",
            "골멩이비방면": "골뱅이비빔면",
            "물냄면": "물냉면",
            "냄면": "냉면",
            "냄": "냉"
        }
        for error, correction in ocr_errors.items():
            cleaned = cleaned.replace(error, correction)
        
        # 연속된 공백 제거
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # 정제된 텍스트가 너무 짧거나 원본과 많이 다르면 원본 반환
        if len(cleaned) < 2 or (len(original) > 4 and len(cleaned) < len(original) * 0.5):
            return original
            
        return cleaned

    def get_serving_size(self, food_name: str) -> int:
        """음식 이름으로 1인분 기준량을 추정합니다."""
        # 기본값은 100g (1인분 정보가 없는 경우)
        default_serving = 100
        
        # 정확한 일치 검색
        if food_name in self.serving_size_guess:
            return self.serving_size_guess[food_name]
        
        # 부분 일치 검색 (가장 긴 일치하는 키워드 찾기)
        matching_items = [(key, value) for key, value in self.serving_size_guess.items() 
                         if key in food_name or food_name in key]
        
        if matching_items:
            # 가장 긴 키워드와 매칭되는 값 반환
            longest_match = max(matching_items, key=lambda x: len(x[0]))
            return longest_match[1]
        
        return default_serving

    def _calculate_per_serving(self, nutrition_info: Dict[str, float], serving_size: int) -> Dict[str, float]:
        """100g 기준 영양성분을 1인분 기준으로 변환합니다."""
        serving_multiplier = serving_size / 100.0
        return {
            "calories": round(nutrition_info["calories"] * serving_multiplier, 1),
            "carbs": round(nutrition_info["carbs"] * serving_multiplier, 1),
            "protein": round(nutrition_info["protein"] * serving_multiplier, 1),
            "fat": round(nutrition_info["fat"] * serving_multiplier, 1)
        }

    async def extract_nutrition_info(self, food_name: str, confidence: float = 1.0) -> Optional[Dict]:
        """음식 이름으로 영양 정보를 검색하고 1인분 기준으로 변환합니다."""
        try:
            # 음식 이름 정제
            cleaned_name = self._clean_food_name(food_name)
            logger.info(f"정제된 음식 이름: {cleaned_name} (원본: {food_name})")
            
            # 식약처 API로 검색
            result = await self._search_food(cleaned_name)
            
            if result:
                # 1인분 기준량 계산
                serving_size = self.get_serving_size(cleaned_name)
                logger.info(f"1인분 기준량: {serving_size}g")

                # 100g 기준 영양성분
                base_nutrition = {
                    "calories": float(result.get('AMT_NUM1', 0)),  # 열량 (kcal)
                    "carbs": float(result.get('AMT_NUM6', 0)),    # 탄수화물 (g)
                    "protein": float(result.get('AMT_NUM3', 0)),  # 단백질 (g)
                    "fat": float(result.get('AMT_NUM4', 0))       # 지방 (g)
                }

                # 1인분 기준으로 변환
                per_serving = self._calculate_per_serving(base_nutrition, serving_size)

                nutrition_info = {
                    "name": cleaned_name,
                    "calories": per_serving["calories"],
                    "nutrients": {
                        "carbohydrates": per_serving["carbs"],
                        "protein": per_serving["protein"],
                        "fat": per_serving["fat"]
                    }
                }
                
                logger.info(f"'{food_name}'의 영양 정보 찾음 (1인분 {serving_size}g 기준): {nutrition_info}")
                return nutrition_info
            
            logger.warning(f"'{food_name}'에 대한 영양 정보를 찾을 수 없음")
            return None
            
        except Exception as e:
            logger.error(f"영양 정보 조회 중 오류 발생: {str(e)}")
            return None

    def get_empty_nutrition(self) -> Dict:
        """빈 영양 정보를 반환합니다."""
        return {
            'name': '',  # 빈 문자열로 설정하여 UI에서 표시되지 않도록 함
            'calories': 0,
            'nutrients': {
                'carbohydrates': 0,
                'protein': 0,
                'fat': 0
            }
        }

    def _find_food_info(self, menu_name: str) -> Optional[Dict]:
        """메뉴의 영양 정보를 찾음"""
        try:
            # 정제된 메뉴명으로 검색
            cleaned_name = self._clean_menu_name(menu_name)
            logger.info(f"정제된 음식 이름: {cleaned_name} ( 원본: {menu_name})")

            # 정확한 매칭 시도
            exact_match = self.nutrition_db[self.nutrition_db['name'] == cleaned_name]
            if not exact_match.empty:
                food_info = exact_match.iloc[0]
                logger.info(f"찾은 음식 (정확한 매칭): {food_info['name']}")
                return self._create_nutrition_info(food_info)

            # 부분 문자열 매칭 시도 (정확도 순으로 정렬)
            partial_matches = []
            for _, food in self.nutrition_db.iterrows():
                food_name = str(food['name'])
                # 메뉴명이 서로 포함 관계인 경우만 검사
                if cleaned_name in food_name or food_name in cleaned_name:
                    # 레벤슈타인 거리 계산
                    distance = self._calculate_levenshtein_distance(cleaned_name, food_name)
                    # 더 짧은 문자열 길이로 정규화
                    normalized_distance = distance / min(len(cleaned_name), len(food_name))
                    
                    # 메뉴명 길이 차이 계산
                    length_diff = abs(len(cleaned_name) - len(food_name))
                    length_ratio = length_diff / min(len(cleaned_name), len(food_name))
                    
                    # 종합 점수 계산 (거리와 길이 차이를 모두 고려)
                    score = normalized_distance + length_ratio
                    
                    partial_matches.append((food, score))

            if partial_matches:
                # 점수가 가장 낮은 것 선택 (가장 유사한 것)
                partial_matches.sort(key=lambda x: x[1])
                best_match = partial_matches[0][0]
                best_score = partial_matches[0][1]
                
                # 점수가 임계값보다 작은 경우에만 매칭 허용
                if best_score <= 0.5:  # 50% 이상 다르면 매칭하지 않음
                    logger.info(f"찾은 음식 (부분 매칭): {best_match['name']} (유사도 점수: {best_score:.2f})")
                    return self._create_nutrition_info(best_match)
                else:
                    logger.info(f"유사도가 너무 낮아서 매칭하지 않음: {best_match['name']} (점수: {best_score:.2f})")
                    return None

            logger.info(f"'{cleaned_name}'에 대한 영양 정보를 찾을 수 없음")
            return None

        except Exception as e:
            logger.error(f"영양 정보 검색 중 오류 발생: {str(e)}")
            return None

    def _calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """레벤슈타인 거리 계산"""
        if len(s1) < len(s2):
            return self._calculate_levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _clean_menu_name(self, menu_name: str) -> str:
        """메뉴명 정제"""
        # 기본 정제
        cleaned = menu_name.strip()
        
        # 공백 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 메뉴 단어 병합
        merge_patterns = {
            r'순두부\s+찌개': '순두부찌개',
            r'김치\s+찌개': '김치찌개',
            r'된장\s+찌개': '된장찌개',
            r'부대\s+찌개': '부대찌개',
            r'참치\s+순두부찌개': '참치순두부찌개',
            r'돼지\s+김치찌개': '돼지김치찌개',
            r'제육\s+덮밥': '제육덮밥',
            r'비빔\s+냉면': '비빔냉면',
            r'물\s+냉면': '물냉면',
            r'오징어\s+볶음': '오징어볶음'
        }
        
        for pattern, replacement in merge_patterns.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned.strip()

    def _create_nutrition_info(self, food_info: pd.Series) -> Dict:
        """영양 정보 딕셔너리 생성"""
        return {
            'name': food_info['name'],
            'calories': float(food_info['calories']),
            'nutrients': {
                'carbohydrates': float(food_info['carbohydrates']),
                'protein': float(food_info['protein']),
                'fat': float(food_info['fat'])
            }
        }