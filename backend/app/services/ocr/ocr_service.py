import easyocr
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        logger.info("OCR 서비스 초기화 중...")
        # 한국어와 영어를 인식하도록 설정
        self.reader = easyocr.Reader(['ko', 'en'])
        logger.info("OCR 서비스 초기화 완료")

    async def extract_text(self, image_bytes: bytes) -> str:
        """
        이미지에서 텍스트를 추출합니다.
        """
        try:
            logger.info("이미지 처리 시작")
            
            # 바이트 데이터를 PIL Image로 변환
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"이미지 크기: {image.size}")
            
            # PIL Image를 numpy array로 변환
            image_np = np.array(image)
            logger.info("이미지를 numpy array로 변환 완료")
            
            # OCR 실행
            logger.info("OCR 텍스트 추출 시작")
            results = self.reader.readtext(image_np)
            logger.info(f"OCR 결과 수: {len(results)}")
            
            # 결과 텍스트 추출 및 결합
            texts = [result[1] for result in results]
            final_text = ' '.join(texts)
            logger.info(f"추출된 전체 텍스트: {final_text}")
            
            return final_text
            
        except Exception as e:
            logger.error(f"OCR 처리 중 오류 발생: {str(e)}")
            raise Exception(f"OCR 처리 중 오류 발생: {str(e)}") 