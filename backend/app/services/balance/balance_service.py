from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, select
from app.models.balance import Meal, User
from app.schemas.balance import Balance,BalanceCreate

logger = logging.getLogger(__name__)

class BalanceService:
    def __init__(self, db: Session):
        self.db = db
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

    def create_balance(self, balance: BalanceCreate) -> Balance:
        db_balance = Meal(
            user_id=balance.user_id,
            meal_type=balance.meal_type,
            menu=balance.menu,
            calories=balance.calories,
            protein=balance.nutrients.get('protein', 0),
            carbs=balance.nutrients.get('carbs', 0),
            fat=balance.nutrients.get('fat', 0),
            fiber=balance.nutrients.get('fiber', 0),
            meal_date=balance.meal_date,
            weather=balance.weather,
            mood=balance.mood,
            exercise=balance.exercise,
            water_intake=balance.water_intake
        )
        self.db.add(db_balance)
        self.db.commit()
        self.db.refresh(db_balance)
        return db_balance

    def get_monthly_balance(self, user_id: int, year: int, month: int) -> dict:
        # 해당 월의 모든 식사 기록 조회
        meals = self.db.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                extract('year', Meal.meal_date) == year,
                extract('month', Meal.meal_date) == month
            )
        ).all()

        # 날짜별로 식사 기록 그룹화
        daily_meals = {}
        for meal in meals:
            date_str = meal.meal_date.strftime("%Y-%m-%d")
            if date_str not in daily_meals:
                daily_meals[date_str] = {
                    "totalCalories": 0,
                    "balanceScore": 0,
                    "meals": [],
                    "weather": meal.weather,
                    "mood": meal.mood,
                    "exercise": meal.exercise,
                    "waterIntake": meal.water_intake
                }
            
            # 식사 정보 추가
            daily_meals[date_str]["meals"].append({
                "type": meal.meal_type,
                "menu": meal.menu,
                "calories": meal.calories,
                "nutrients": {
                    "protein": meal.protein,
                    "carbs": meal.carbs,
                    "fat": meal.fat,
                    "fiber": meal.fiber
                },
                "tags": self._generate_tags(meal)
            })
            
            # 총 칼로리 계산
            daily_meals[date_str]["totalCalories"] += meal.calories
            
            # 밸런스 점수 계산
            daily_meals[date_str]["balanceScore"] = self.calculate_balance_score({
                "protein": meal.protein.real,
                "carbs": meal.carbs.real,
                "fat": meal.fat.real,
                "fiber": meal.fiber.real
            })

        return daily_meals

    def get_user_stats(self, user_id: int) -> dict:
        # 현재 달의 통계 계산
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        monthly_meals = self.db.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                Meal.meal_date >= start_of_month,
                Meal.meal_date <= end_of_month
            )
        ).all()

        # 통계 계산
        total_balance = 0
        total_calories = 0
        breakfast_count = 0
        meal_counts = {}
        water_goal_achieved = 0

        for meal in monthly_meals:
            # 밸런스 점수
            balance_score = self.calculate_balance_score({
                "protein": meal.protein.real,
                "carbs": meal.carbs.real,
                "fat": meal.fat.real,
                "fiber": meal.fiber.real
            })
            total_balance += balance_score
            
            # 칼로리
            total_calories += meal.calories.real
            
            # 아침 식사 횟수
            if str(meal.meal_type) == "breakfast":
                breakfast_count += 1
            
            # 가장 자주 먹은 음식
            if meal.menu in meal_counts:
                meal_counts[meal.menu] += 1
            else:
                meal_counts[meal.menu] = 1
            
            # 물 섭취 목표 달성
            if meal.water_intake >= 2000:
                water_goal_achieved += 1

        days_in_month = (end_of_month - start_of_month).days + 1
        meals_count = len(monthly_meals)

        return {
            "averageBalance": round(total_balance / days_in_month if days_in_month > 0 else 0, 1),
            "averageCalories": round(total_calories / days_in_month if days_in_month > 0 else 0),
            "waterGoalAchievement": round((water_goal_achieved / days_in_month) * 100 if days_in_month > 0 else 0),
            "breakfastCount": breakfast_count,
            "mostFrequentMenu": max(meal_counts.items(), key=lambda x: x[1])[0] if meal_counts else None,
            "preferredMealTime": self._get_preferred_meal_time(user_id)
        }

    def get_user_streak(self, user_id: int) -> dict:
        # 최근 60일간의 기록 조회
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)
        
        meals = self.db.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                Meal.meal_date >= start_date,
                Meal.meal_date <= end_date
            )
        ).order_by(Meal.meal_date.desc()).all()

        # 날짜별 식사 기록 그룹화
        daily_records = {}
        for meal in meals:
            date_str = meal.meal_date.strftime("%Y-%m-%d")
            if date_str not in daily_records:
                daily_records[date_str] = {
                    "meals": [],
                    "perfect": False
                }
            daily_records[date_str]["meals"].append(meal)

        # 완벽한 날 계산 (3끼 식사 + 물 2L 이상)
        for date_str, record in daily_records.items():
            meal_types = set(meal.meal_type for meal in record["meals"])
            water_intake = sum(meal.water_intake for meal in record["meals"])
            record["perfect"] = len(meal_types) >= 3 and water_intake >= 2000

        # 현재 연속일수 계산
        current_streak = 0
        current_date = end_date
        while current_date >= start_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in daily_records and daily_records[date_str]["perfect"]:
                current_streak += 1
            else:
                break
            current_date -= timedelta(days=1)

        # 최장 연속일수 계산
        longest_streak = 0
        current_streak_count = 0
        perfect_days = 0

        for i in range((end_date - start_date).days + 1):
            check_date = start_date + timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            
            if date_str in daily_records and daily_records[date_str]["perfect"]:
                current_streak_count += 1
                perfect_days += 1
                longest_streak = max(longest_streak, current_streak_count)
            else:
                current_streak_count = 0

        return {
            "currentStreak": current_streak,
            "longestStreak": longest_streak,
            "totalPerfectDays": perfect_days
        }

    def _generate_tags(self, meal: Meal) -> List[str]:
        tags = []
        
        # 칼로리 기반 태그
        if meal.calories.real < 400:
            tags.append("저칼로리")
        elif meal.calories.real > 800:
            tags.append("고칼로리")
            
        # 단백질 기반 태그
        if meal.protein.real > 30:
            tags.append("고단백")
            
        # 탄수화물 기반 태그
        if meal.carbs.real < 30:
            tags.append("저탄수화물")
            
        # 지방 기반 태그
        if meal.fat.real < 10:
            tags.append("저지방")
            
        # 식이섬유 기반 태그
        if meal.fiber.real > 8:
            tags.append("식이섬유 풍부")
            
        return tags

    def _get_preferred_meal_time(self, user_id: int) -> str:
        # 가장 자주 먹는 시간대 계산
        meal_times = self.db.query(
            func.date_part('hour', Meal.meal_date).label('hour'),
            func.count().label('count')
        ).filter(
            Meal.user_id == user_id
        ).group_by(
            func.date_part('hour', Meal.meal_date)
        ).order_by(
            func.count().desc()
        ).first()

        if meal_times:
            hour = int(meal_times[0])
            return f"{hour:02d}:00"
        return "12:00" 