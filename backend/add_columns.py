import sqlite3

def add_columns():
    # 데이터베이스 연결
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.cursor()

    try:
        # users 테이블에 새로운 컬럼 추가
        cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
        print("Added password_hash column to users table")
        
        # email 컬럼을 NOT NULL로 변경하기 위해 임시 테이블 생성
        cursor.execute('''
            CREATE TABLE users_temp (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT,
                profile_image TEXT,
                daily_calorie_goal INTEGER DEFAULT 2000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 기존 데이터를 임시 테이블로 복사
        cursor.execute('''
            INSERT INTO users_temp (id, email, password_hash, name, profile_image, daily_calorie_goal, created_at)
            SELECT id, COALESCE(email, 'temp_' || id || '@example.com'), 
                   COALESCE(password_hash, 'temp_password'), name, profile_image, 
                   daily_calorie_goal, created_at
            FROM users
        ''')
        
        # 기존 테이블 삭제
        cursor.execute('DROP TABLE users')
        
        # 임시 테이블 이름 변경
        cursor.execute('ALTER TABLE users_temp RENAME TO users')
        
        # 변경사항 저장
        conn.commit()
        print("Successfully updated users table schema")
        
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        # 이미 컬럼이 존재하는 경우 무시
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns() 