from sqlalchemy import create_engine
from app.models.balance import Base, User, Meal
from app.database import SQLALCHEMY_DATABASE_URL

# 데이터베이스 연결
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def clear_tables():
    # 세션 생성
    connection = engine.connect()
    
    try:
        # 테이블의 모든 데이터 삭제
        connection.execute(Meal.__table__.delete())
        connection.execute(User.__table__.delete())
        
        # 변경사항 커밋
        connection.commit()
        print("모든 데이터가 성공적으로 삭제되었습니다.")
        
    except Exception as e:
        print(f"데이터 삭제 중 오류 발생: {str(e)}")
        
    finally:
        # 연결 종료
        connection.close()

if __name__ == "__main__":
    clear_tables() 