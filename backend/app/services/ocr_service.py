from fastapi import UploadFile
import easyocr
from PIL import Image
import io
import re

class OCRService:
    def __init__(self):
        # 한글과 영어를 인식하는 OCR 리더 초기화
        self.reader = easyocr.Reader(['ko', 'en'])

    async def extract_text(self, file: UploadFile) -> str:
        """
        이미지에서 텍스트를 추출하고 음식 관련 정보를 필터링
        """
        # 이미지 읽기
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # OCR 수행
        result = self.reader.readtext(image)
        
        # 결과 텍스트 추출 (신뢰도 50% 이상)
        texts = [text for _, text, conf in result if float(conf) > 0.5]
        full_text = " ".join(texts)
        
        # 음식 관련 정보 필터링 (메뉴명, 칼로리 등)
        food_info = self._filter_food_info(full_text)
        
        return food_info
    
    def _filter_food_info(self, text: str) -> str:
        """
        텍스트에서 음식 관련 정보만 필터링
        """
        # 칼로리 정보 찾기
        calories = re.findall(r'\d+\s*kcal', text)
        
        # 영양소 정보 찾기
        nutrients = re.findall(r'(단백질|지방|탄수화물|섬유질)[\s:]*([\d.]+)g?', text)
        
        # 메뉴명 찾기 (한글 단어들)
        menu_items = re.findall(r'[가-힣\s]+', text)
        
        filtered_text = ""
        if menu_items:
            filtered_text += f"메뉴: {', '.join(menu_items)} "
        if calories:
            filtered_text += f"칼로리: {', '.join(calories)} "
        if nutrients:
            filtered_text += f"영양소: {', '.join([f'{n[0]} {n[1]}g' for n in nutrients])}"
            
        return filtered_text.strip() 