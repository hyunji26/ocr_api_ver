import pandas as pd

# 엑셀 파일 읽기
excel_file = "C:/Users/PC2412/Downloads/20250408_음식DB.xlsx"
df = pd.read_excel(excel_file)

# CSV 파일로 저장 (UTF-8 인코딩 사용)
df.to_csv("nutrition_db.csv", index=False, encoding='euc-kr') 