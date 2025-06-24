import os
import sqlite3
from datetime import datetime

# backend 디렉토리를 기준으로 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 디렉토리
DB_PATH = os.path.join(CURRENT_DIR, "backend", "sql_app.db")  # backend 디렉토리의 데이터베이스

print(f"현재 디렉토리: {CURRENT_DIR}")
print(f"데이터베이스 경로: {DB_PATH}")

def update_timestamps(cursor):
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(f"UPDATE meals SET timestamp = '{current_date} ' || substr(timestamp, 12) WHERE date(timestamp) > '2024-01-01'")
        cursor.execute(f"UPDATE users SET created_at = '{current_date} ' || substr(created_at, 12) WHERE date(created_at) > '2024-01-01'")
        print("\n날짜 업데이트 완료")
    except sqlite3.Error as e:
        print(f"날짜 업데이트 중 오류 발생: {e}")

def print_table_data(cursor, table_name):
    try:
        print(f"\n=== {table_name} 테이블 데이터 ===")
        # 테이블 스키마 출력
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("\n컬럼 정보:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # 데이터 출력
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"\n총 {len(rows)}개의 레코드:")
        for row in rows:
            print(row)
    except sqlite3.Error as e:
        print(f"테이블 {table_name} 조회 중 오류 발생: {e}")

def main():
    try:
        # 데이터베이스 연결
        print(f"\n데이터베이스 연결 시도... ({DB_PATH})")
        conn = sqlite3.connect("backend/sql_app.db")  # 경로 수정
        cursor = conn.cursor()
        
        # 날짜 업데이트
        update_timestamps(cursor)
        conn.commit()
        
        # 모든 테이블 목록 가져오기
        print("\n테이블 목록 조회 중...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("데이터베이스에 테이블이 없습니다!")
            return
            
        print("=== 데이터베이스 테이블 목록 ===")
        for table in tables:
            table_name = table[0]
            print(f"\n테이블 이름: {table_name}")
            print_table_data(cursor, table_name)
        
        conn.close()
        print("\n데이터베이스 연결 종료")
    except sqlite3.Error as e:
        print(f"데이터베이스 오류 발생: {e}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main() 