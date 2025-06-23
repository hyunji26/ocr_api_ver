from datetime import datetime
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class BalanceService:
    def __init__(self):
        # 권장 영양소 비율 (각 범위의 중간값 사용)
        # 탄수화물: 45-65% -> 55%
        # 단백질: 10-35% -> 22.5%
        # 지방: 20-35% -> 27.5%
        self.recommended_ratio = {
            'carbohydrates': 0.55,  # 55%
            'protein': 0.225,       # 22.5%
            'fat': 0.275           # 27.5%
        }
        
        # 권장 영양소 범위
        self.nutrient_ranges = {
            'carbohydrates': (0.45, 0.65),  # 45-65%
            'protein': (0.10, 0.35),        # 10-35%
            'fat': (0.20, 0.35)            # 20-35%
        }

    def calculate_balance_score(self, nutrients: Dict[str, float]) -> float:
        """
        영양소 비율을 기반으로 밸런스 점수를 계산
        
        Args:
            nutrients: {'carbohydrates': float, 'protein': float, 'fat': float}
            
        Returns:
            float: 0-100 사이의 밸런스 점수
        """
        try:
            # 실제 영양소 총합 계산
            total = sum(nutrients.values())
            
            if total == 0:
                return 0
            
            # 실제 비율 계산
            actual_ratio = {
                nutrient: value/total for nutrient, value in nutrients.items()
            }
            
            # 점수 계산 (100점 만점)
            score = 100
            
            # 각 영양소에 대해 권장 범위를 벗어난 정도에 따라 감점
            for nutrient, (min_ratio, max_ratio) in self.nutrient_ranges.items():
                actual = actual_ratio[nutrient]
                if actual < min_ratio:
                    score -= (min_ratio - actual) * 100
                elif actual > max_ratio:
                    score -= (actual - max_ratio) * 100
            
            return max(0, min(100, round(score)))
            
        except Exception as e:
            logger.error(f"밸런스 점수 계산 중 오류 발생: {str(e)}")
            return 0

    def analyze_nutrients(self, nutrients: Dict[str, float]) -> Dict[str, str]:
        """
        영양소 섭취 현황을 분석하여 베스트/개선 영양소를 결정
        
        Args:
            nutrients: {'carbohydrates': float, 'protein': float, 'fat': float}
            
        Returns:
            Dict: {'highlight': str, 'needsImprovement': str}
        """
        try:
            # 실제 영양소 총합 계산
            total = sum(nutrients.values())
            
            if total == 0:
                return {
                    'highlight': '탄수화물',  # 기본값
                    'needsImprovement': '단백질'  # 기본값
                }
            
            # 실제 비율 계산
            actual_ratios = {
                nutrient: value/total for nutrient, value in nutrients.items()
            }
            
            # 각 영양소의 권장 범위 이탈 정도 계산
            deviations = {}
            for nutrient, (min_ratio, max_ratio) in self.nutrient_ranges.items():
                actual = actual_ratios[nutrient]
                if actual < min_ratio:
                    deviations[nutrient] = min_ratio - actual
                elif actual > max_ratio:
                    deviations[nutrient] = actual - max_ratio
                else:
                    deviations[nutrient] = 0
            
            # 가장 권장범위에 잘 맞는 영양소와 가장 많이 벗어난 영양소 찾기
            highlight = min(deviations.items(), key=lambda x: x[1])[0]
            needs_improvement = max(deviations.items(), key=lambda x: x[1])[0]
            
            # 한글 변환
            nutrient_names = {
                'carbohydrates': '탄수화물',
                'protein': '단백질',
                'fat': '지방'
            }
            
            return {
                'highlight': nutrient_names[highlight],
                'needsImprovement': nutrient_names[needs_improvement]
            }
            
        except Exception as e:
            logger.error(f"영양소 분석 중 오류 발생: {str(e)}")
            return {
                'highlight': '탄수화물',
                'needsImprovement': '단백질'
            }

    def calculate_last_meal_time(self, meals: list) -> str:
        """
        마지막 식사 시간 계산
        
        Args:
            meals: 식사 기록 리스트
            
        Returns:
            str: "n시간 전" 형식의 문자열
        """
        try:
            if not meals:
                return "0시간 전"
            
            last_meal_time = max(meal.timestamp for meal in meals)
            time_diff = datetime.now() - last_meal_time
            
            hours = time_diff.total_seconds() / 3600
            if hours < 1:
                return "0시간 전"
            return f"{int(hours)}시간 전"
            
        except Exception as e:
            logger.error(f"마지막 식사 시간 계산 중 오류 발생: {str(e)}")
            return "0시간 전" 