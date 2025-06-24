from app.database import Base, engine, SessionLocal
from app.models.balance import Meal, User
from datetime import datetime

def add_test_data():
    # 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # DB 세션 생성
    db = SessionLocal()
    
    try:
        # 2025년 6월 23일 식사 데이터 추가
        test_meals = [
            Meal(
                user_id=1,
                meal_type="breakfast",
                food_name="현미밥과 계란말이",
                timestamp=datetime(2025, 6, 23, 8, 30),
                calories=350,
                carbohydrates=45,
                protein=15,
                fat=8
            ),
            Meal(
                user_id=1,
                meal_type="breakfast",
                food_name="우유",
                timestamp=datetime(2025, 6, 23, 8, 30),
                calories=120,
                carbohydrates=12,
                protein=8,
                fat=4
            ),
            Meal(
                user_id=1,
                meal_type="lunch",
                food_name="김치찌개와 공기밥",
                timestamp=datetime(2025, 6, 23, 12, 30),
                calories=550,
                carbohydrates=65,
                protein=25,
                fat=15
            ),
            Meal(
                user_id=1,
                meal_type="lunch",
                food_name="오이무침",
                timestamp=datetime(2025, 6, 23, 12, 30),
                calories=50,
                carbohydrates=8,
                protein=2,
                fat=1
            ),
            Meal(
                user_id=1,
                meal_type="dinner",
                food_name="닭가슴살 샐러드",
                timestamp=datetime(2025, 6, 23, 18, 30),
                calories=300,
                carbohydrates=10,
                protein=40,
                fat=12
            ),
            Meal(
                user_id=1,
                meal_type="dinner",
                food_name="통밀빵",
                timestamp=datetime(2025, 6, 23, 18, 30),
                calories=150,
                carbohydrates=28,
                protein=6,
                fat=2
            )
        ]
        
        # 데이터 추가
        for meal in test_meals:
            db.add(meal)
        
        # 변경사항 저장
        db.commit()
        print('테스트 데이터가 성공적으로 추가되었습니다.')
        
    except Exception as e:
        print(f'에러 발생: {str(e)}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_data() 