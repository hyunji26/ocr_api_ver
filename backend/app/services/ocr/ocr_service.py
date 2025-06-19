import easyocr
import logging
import numpy as np
from PIL import Image
import io
import re
from difflib import SequenceMatcher, get_close_matches
import hgtk  # 한글 자모 분리/결합 라이브러리
from app.services.nutrition.data.menu_dict_generator import get_menu_dict
from typing import List, Tuple

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        logger.info("OCR 서비스 초기화 중...")
        # 한국어와 영어를 인식하도록 설정
        self.reader = easyocr.Reader(['ko', 'en'])
        
        # 메뉴 목록 초기화
        self.menu_set = get_menu_dict('app/services/nutrition/data/nutrition_db.csv')
        
        # 영문 메뉴 매핑
        self.eng_to_kor = {
            "MANDUGUK": "만두국",
            "GALBITUNG": "갈비탕",
            "BIBIMBAP": "비빔밥",
            "KIMCHIJJIGAE": "김치찌개",
            "DOENJANGJJIGAE": "된장찌개",
            "BUDAEJJIGAE": "부대찌개"
        }

        # 자주 발생하는 OCR 오류 수정
        self.common_ocr_errors = {
            "째개": "찌개",
            "찌게": "찌개",
            "덜밥": "덮밥",
            "방밥": "빔밥",  # 비빔밥 오류 처리
            "비방": "비빔",  # 비빔밥 오류 처리
            "공": "콤",      # 매콤한 -> 매공한 오류 처리
            "른": "큰",      # 얼큰한 -> 얼른한 오류 처리
        }

        self.modifiers = [
            # 맛 관련
            "매콤한", "매운", "달콤한", "달콤", "얼큰한", "얼큰", "맵고", "맛있는",
            "고소한", "신선한", "따뜻한", "따듯한", "차가운", "시원한", "짭짤한", "달달한",
            "진한", "깔끔한", "풍미가득", "향긋한", "담백한", "부드러운", "기분좋은",
            
            # 상태/품질 관련
            "특제", "특별한", "새로운", "인기", "최고", "추천", "모듬", "모둠", "정통", "전통",
            "정성껏", "프리미엄", "수제", "수제비", "장인의", "명품", "정통", "오리지널", "자연산",

            # 시간 관련
            "아침", "점심", "저녁", "밤", "새벽", "브런치", "런치", "디너", "심야",

            # 크기/양 관련
            "큰", "작은", "많은", "적은", "곱빼기", "특대", "대왕", "한입", "소형", "미니", "점보",

            # 온도 관련
            "따뜻하게", "시원하게", "뜨거운", "차가운", "데운", "식은",

            # 기타 수식어
            "즉석", "직화", "바로", "얼른", "촉촉한", "쫄깃한", "담백한", "구수한", "사르르",
            "깔끔한", "가성비", "고퀄리티", "재방문", "베스트", "비건", "헬시", "웰빙", "국산",

            # 세트/구성 관련
            "세트", "정식", "SET", "사이드", "콤보", "런치박스", "A세트", "B세트", "특선", "단품",

            # 외국어 표현 (브랜딩 용어)
            "Best", "Hot", "New", "Premium", "Special", "Deluxe", "Signature", "Chef's", "Real"
        ]

        
        logger.info("OCR 서비스 초기화 완료")

    def _decompose_hangul(self, text):
        """한글 문자를 자모 단위로 분리"""
        try:
            return [hgtk.text.decompose(char) if hgtk.checker.is_hangul(char) else char for char in text]
        except Exception as e:
            logger.warning(f"한글 자모 분리 중 오류 발생: {str(e)}")
            return list(text)

    def _compose_hangul(self, decomposed):
        """자모를 한글 문자로 결합"""
        try:
            return ''.join([hgtk.text.compose(char) if isinstance(char, str) and 'ᄀ' <= char[0] <= 'ᇿ' else char for char in decomposed])
        except Exception as e:
            logger.warning(f"한글 자모 결합 중 오류 발생: {str(e)}")
            return ''.join(decomposed)

    def _convert_eng_to_kor(self, text):
        """영문 메뉴를 한글로 변환"""
        # 대문자로 변환하고 공백 제거
        text_upper = ''.join(text.upper().split())
        
        # 영문 메뉴 매핑에서 찾기
        if text_upper in self.eng_to_kor:
            return self.eng_to_kor[text_upper]
            
        # 부분 매칭 시도
        for eng, kor in self.eng_to_kor.items():
            if text_upper in eng or eng in text_upper:
                return kor
                
        return text

    def _find_best_menu_match(self, text):
        """메뉴 사전에서 가장 유사한 메뉴 찾기 (set 기반)"""
        # 영문인 경우 한글로 변환 시도
        if re.match(r'^[A-Za-z\s]+$', text):
            text = self._convert_eng_to_kor(text)

        best_score = 0
        best_match = text

        # 입력 텍스트의 자모 분리
        text_decomposed = self._decompose_hangul(text)

        for correct_menu in self.menu_set:  # ✅ dict -> set
            # 자모 단위 유사도 비교
            correct_decomposed = self._decompose_hangul(correct_menu)
            score = SequenceMatcher(None, str(text_decomposed), str(correct_decomposed)).ratio()

            # 유사도가 매우 높은 경우(0.8 이상)에만 매칭
            if score > best_score and score > 0.8:
                best_score = score
                best_match = correct_menu

        # 충분히 높은 유사도를 가진 매칭이 없으면 원본 반환
        return best_match if best_score > 0.8 else text

    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        # 1. 특수문자 제거 (한글, 영문, 숫자, 공백만 남김)
        text = re.sub(r'[^ㄱ-ㅎ가-힣a-zA-Z0-9\s]', '', text)
        
        # 2. 숫자와 단위 제거 (예: 258g)
        text = re.sub(r'\d+[gmkl]+', '', text)
        text = re.sub(r'\d+', '', text)
        
        # 3. OCR 오류 수정
        for error, correction in self.common_ocr_errors.items():
            text = text.replace(error, correction)
        
        # 4. 여러 공백을 하나의 공백으로
        text = re.sub(r'\s+', ' ', text)
        
        # 5. 앞뒤 공백 제거
        return text.strip()

    def _remove_modifiers(self, text: str) -> str:
        """수식어 제거"""
        # 수식어 제거
        for modifier in self.modifiers:
            text = re.sub(rf'\b{modifier}\b', '', text, flags=re.IGNORECASE)
        
        # 여러 공백을 하나의 공백으로
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _exact_match_exists(self, text: str) -> str:
        """메뉴 목록에서 정확히 일치하는 메뉴 찾기"""
        if text in self.menu_set:
            return text
        return None

    def _contains_menu(self, text: str) -> str:
        """텍스트에 포함된 메뉴 찾기"""
        # 가장 긴 메뉴부터 확인 (예: "김치찌개" vs "찌개")
        sorted_menus = sorted(self.menu_set, key=len, reverse=True)
        for menu in sorted_menus:
            if menu in text:
                return menu
        return None

    def _calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """레벤슈타인 거리 계산 (Java 코드 참고)"""
        # 2차원 DP 배열 초기화
        dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
        
        # 첫 행과 열 초기화
        for i in range(len(s1) + 1):
            dp[i][0] = i
        for j in range(len(s2) + 1):
            dp[0][j] = j
            
        # DP로 최소 편집 거리 계산
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j-1],  # 대체
                        dp[i-1][j],    # 삭제
                        dp[i][j-1]     # 삽입
                    )
                    
        return dp[len(s1)][len(s2)]

    def normalize_menu(self, text: str) -> str:
        """메뉴 이름을 정규화"""
        # 영문 메뉴를 한글로 변환
        if text.upper() in self.eng_to_kor:
            text = self.eng_to_kor[text.upper()]
        
        # OCR 오류 수정
        for error, correction in self.common_ocr_errors.items():
            text = text.replace(error, correction)
        
        # 수식어 제거
        for modifier in self.modifiers:
            text = text.replace(modifier, "")
        
        # 공백 제거
        text = text.strip()
        
        # 메뉴 목록에서 가장 유사한 메뉴 찾기
        try:
            matches = get_close_matches(text, self.menu_set, n=1, cutoff=0.6)
            if matches:
                return matches[0]
        except Exception as e:
            logger.warning(f"유사도 계산 중 오류 발생: {str(e)}")
        
        return text

    def extract_menu_from_text(self, text: str) -> str:
        """텍스트에서 메뉴 이름 추출"""
        try:
            # 텍스트 전처리
            text = text.strip()
            if not text:
                return None

            # 영문 메뉴를 한글로 변환
            if text.upper() in self.eng_to_kor:
                return self.eng_to_kor[text.upper()]

            # 한글 자모 분리
            text_decomposed = self._decompose_hangul(text)

            # 메뉴 목록에서 가장 유사한 메뉴 찾기
            normalized_menu = self.normalize_menu(text)
            if normalized_menu in self.menu_set:
                return normalized_menu

            # 유사도가 높은 메뉴가 없으면 None 반환
            return None

        except Exception as e:
            logger.error(f"메뉴 추출 중 오류 발생: {str(e)}")
            return None

    def _find_menu_in_text(self, text: str) -> List[str]:
        """텍스트에서 가능한 메뉴 조합을 찾음"""
        words = text.split()
        candidates = []
        
        # 1. 전체 텍스트를 하나의 후보로
        candidates.append(text)
        
        # 2. 연속된 단어들의 조합을 후보로
        for i in range(len(words)):
            for j in range(i + 1, len(words) + 1):
                candidate = ' '.join(words[i:j])
                if candidate != text:  # 전체 텍스트와 같지 않은 경우만
                    candidates.append(candidate)
        
        return candidates

    def extract_menu_from_text_with_similarity(self, text: str) -> Tuple[str, float]:
        """텍스트에서 메뉴 이름과 유사도를 함께 추출"""
        try:
            # 텍스트 전처리
            text = text.strip()
            if not text:
                return None, 0.0

            # 영문 메뉴를 한글로 변환
            if text.upper() in self.eng_to_kor:
                return self.eng_to_kor[text.upper()], 1.0

            # 1단계: 기본 정규화
            normalized_text = self._normalize_text(text)
            if not normalized_text:
                return None, 0.0
            
            # 2단계: 수식어 제거
            clean_text = self._remove_modifiers(normalized_text)
            if not clean_text:
                clean_text = normalized_text

            # 3단계: 정확한 매칭 시도
            exact_match = self._exact_match_exists(clean_text)
            if exact_match:
                logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {exact_match} (정확히 일치)")
                return exact_match, 1.0

            # 4단계: 포함된 메뉴 찾기
            contained_menu = self._contains_menu(clean_text)
            if contained_menu:
                logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {contained_menu} (부분 일치)")
                return contained_menu, 0.9

            # 5단계: 단어 단위로 분리하여 매칭
            words = clean_text.split()
            best_match = None
            min_distance = float('inf')
            
            # 각 메뉴에 대해
            for menu in self.menu_set:
                menu_words = set(menu.split())
                
                # 입력 텍스트의 각 단어에 대해
                for word in words:
                    # 단어가 메뉴의 일부인 경우
                    if word in menu:
                        distance = self._calculate_levenshtein_distance(clean_text, menu)
                        if distance < min_distance:
                            min_distance = distance
                            best_match = menu

            if best_match:
                similarity = 1.0 - (min_distance / max(len(clean_text), len(best_match)))
                logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {best_match} (유사도: {similarity:.2f})")
                return best_match, similarity

            # 6단계: 마지막으로 레벤슈타인 거리로 시도
            best_match = None
            min_distance = float('inf')
            
            for menu in self.menu_set:
                distance = self._calculate_levenshtein_distance(clean_text, menu)
                if distance < min_distance and distance <= len(menu) // 2:  # 거리가 메뉴 길이의 절반 이하인 경우만
                    min_distance = distance
                    best_match = menu

            if best_match:
                similarity = 1.0 - (min_distance / max(len(clean_text), len(best_match)))
                logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {best_match} (레벤슈타인 거리: {min_distance}, 유사도: {similarity:.2f})")
                return best_match, similarity

            return None, 0.0

        except Exception as e:
            logger.error(f"메뉴 추출 중 오류 발생: {str(e)}")
            return None, 0.0

    async def extract_text(self, image_bytes: bytes) -> List[dict]:
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
                    # 가격 정보는 제외
                    if re.match(r'^\d+,?\d*원?$', text.strip()):
                        continue

                    # 텍스트 정규화
                    normalized_text = self._normalize_text(text)
                    
                    # 빈 문자열이 되면 건너뛰기
                    if not normalized_text:
                        continue

                    extracted_results.append({
                        "original_text": text.strip(),
                        "text": normalized_text,
                        "confidence": round(confidence, 2)
                    })
            
            # 결과 반환 전에 모든 추출된 텍스트를 로그에 출력
            for result in extracted_results:
                logger.info(f"원본 텍스트: {result['original_text']} -> 정제된 텍스트: {result['text']} (신뢰도: {result['confidence']:.2f})")
            
            return extracted_results
            
        except Exception as e:
            logger.error(f"텍스트 추출 중 오류 발생: {str(e)}")
            return []

    def process_image(self, image_data: bytes) -> List[str]:
        """이미지에서 메뉴 텍스트 추출"""
        try:
            # 이미지를 numpy array로 변환
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)
            logger.info("이미지를 numpy array로 변환 완료")
            
            # OCR 텍스트 추출
            logger.info("OCR 텍스트 추출 시작")
            results = self.reader.readtext(image_np)
            
            # 추출된 텍스트 목록
            extracted_texts = [result[1] for result in results]
            logger.info(f"OCR 결과 수: {len(extracted_texts)}")
            
            # 메뉴 추출 및 중복 제거
            menus = []
            for text in extracted_texts:
                menu = self.extract_menu_from_text(text)
                if menu and menu not in menus:
                    menus.append(menu)
            
            return menus
            
        except Exception as e:
            logger.error(f"텍스트 추출 중 오류 발생: {str(e)}")
            return []  # 에러 발생 시 빈 리스트 반환
