from sqlalchemy import create_engine
from app.models.balance import User
from app.database import SQLALCHEMY_DATABASE_URL
from sqlalchemy.orm import sessionmaker

# 데이터베이스 연결
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_users():
    # 세션 생성
    db = SessionLocal()
    
    try:
        # 모든 사용자 조회
        users = db.query(User).all()
        
        print("\n=== 사용자 목록 ===")
        for user in users:
            print(f"ID: {user.id}")
            print(f"이름: {user.name}")
            print(f"이메일: {user.email}")
            print(f"일일 칼로리 목표: {user.daily_calorie_goal}")
            print("-" * 20)
        
    except Exception as e:
        print(f"데이터베이스 조회 중 오류 발생: {str(e)}")
        
    finally:
        # 연결 종료
        db.close()

if __name__ == "__main__":
    check_users() 