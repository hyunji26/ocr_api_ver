from sqlalchemy import create_engine
from app.models.balance import Base, User, Meal
from app.database import SQLALCHEMY_DATABASE_URL
from sqlalchemy.orm import sessionmaker

# 데이터베이스 연결
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def clear_tables():
    # 세션 생성
    db = SessionLocal()
    
    try:
        # 테이블의 모든 데이터 삭제
        db.query(Meal).delete()
        db.query(User).delete()
        
        # 변경사항 커밋
        db.commit()
        print("모든 데이터가 성공적으로 삭제되었습니다.")
        
    except Exception as e:
        db.rollback()
        print(f"데이터 삭제 중 오류 발생: {str(e)}")
        
    finally:
        # 연결 종료
        db.close()

if __name__ == "__main__":
    clear_tables() 