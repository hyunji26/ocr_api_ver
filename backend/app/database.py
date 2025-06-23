import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# backend 디렉토리를 기준으로 경로 설정
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend 디렉토리
DB_PATH = os.path.join(CURRENT_DIR, "sql_app.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

print(f"데이터베이스 설정 - 경로: {DB_PATH}")

# 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    print(f"테이블 생성 시작 - DB 경로: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료")
    
    # 기본 사용자 생성
    db = SessionLocal()
    try:
        # users 테이블에 데이터가 있는지 확인
        result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if result == 0:
            # 기본 사용자 추가 (ID: 1)
            db.execute(text("INSERT INTO users (id, daily_calorie_goal) VALUES (1, 2000)"))
            db.commit()
            print("기본 사용자 생성 완료")
    except Exception as e:
        db.rollback()
        print(f"기본 사용자 생성 중 오류 발생: {str(e)}")
    finally:
        db.close()

__all__ = ['engine', 'SessionLocal', 'Base', 'get_db', 'create_tables'] 