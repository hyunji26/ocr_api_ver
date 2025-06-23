import sys
print("=== Python 환경 정보 ===")
print(f"Python 실행 경로: {sys.executable}")
print(f"\nPython 버전: {sys.version}")
print("\n패키지 설치 경로:")
for path in sys.path:
    if 'site-packages' in path:
        print(f"- {path}") 