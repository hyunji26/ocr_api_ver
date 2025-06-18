import easyocr
import logging
import numpy as np
from PIL import Image
import io
import re

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        logger.info("OCR 서비스 초기화 중...")
        # 한국어와 영어를 인식하도록 설정
        self.reader = easyocr.Reader(['ko', 'en'])
        logger.info("OCR 서비스 초기화 완료")

    async def extract_text(self, image_bytes):
        try:
            logger.info("이미지 처리 시작")
            
            # 바이트 데이터를 PIL Image로 변환
            image = Image.open(io.BytesIO(image_bytes))
            
            # PIL Image를 numpy array로 변환
            image_np = np.array(image)
            logger.info("이미지를 numpy array로 변환 완료")
            
            # OCR 실행
            logger.info("OCR 텍스트 추출 시작")
            results = self.reader.readtext(image_np)
            logger.info(f"OCR 결과 수: {len(results)}")
            
            # 결과가 없는 경우
            if not results:
                logger.info("텍스트가 발견되지 않았습니다.")
                return []
            
            # 모든 텍스트와 신뢰도 추출
            extracted_results = []
            for bbox, text, confidence in results:
                # 한글, 영문, 숫자, 공백만 포함된 텍스트 허용
                if re.match(r'^[가-힣a-zA-Z0-9\s]+$', text.strip()):
                    text = text.strip()
                    extracted_results.append({
                        "text": text,
                        "confidence": round(confidence, 2)
                    })
            
            # 결과 반환 전에 모든 추출된 텍스트를 로그에 출력
            logger.info(f"OCR 결과 수: {len(extracted_results)}")
            for result in extracted_results:
                logger.info(f"추출된 텍스트: {result['text']} (신뢰도: {result['confidence']:.2f})")
            
            return extracted_results
            
        except Exception as e:
            logger.error(f"텍스트 추출 중 오류 발생: {str(e)}")
            raise e
