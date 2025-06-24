import easyocr
import logging
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
import cv2
from difflib import SequenceMatcher, get_close_matches
import hgtk  # 한글 자모 분리/결합 라이브러리
from app.services.nutrition.data.menu_dict_generator import get_menu_dict
from typing import List, Tuple, Optional

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

        # 메뉴가 아닌 텍스트 패턴
        self.non_menu_patterns = [
            r'^SINCE\s+\d+',  # SINCE 1780 같은 패턴
            r'^\d{2,}$',      # 숫자만 있는 경우
            r'^\d{2,3}-?\d{3,4}-?\d{4}$',  # 전화번호
            r'.*[백반집|식당|레스토랑].*',   # 가게 이름
            r'^[A-Za-z\s\d]+$',  # 영어로만 된 텍스트
        ]
        
        # 자주 발생하는 OCR 오류 수정
        self.common_ocr_errors = {
            "째개": "찌개",
            "찌게": "찌개",
            "덜밥": "덮밥",
            "댐밥": "덮밥",
            "방밥": "밥",
            "비방": "비빔",
            "멩이": "뱅이",
            "콜면이": "골뱅이",
            "째": "찌개",     # "부대째" -> "부대찌개"
            "불고": "불고기",  # "불고 덮밥" -> "불고기덮밥"
            "비범": "비빔",    # "육회비범밥" -> "육회비빔밥"
            "뷰음": "볶음",    # "오징어뷰음" -> "오징어볶음"
            "뒷밥": "덮밥"     # "제육뒷밥" -> "제육덮밥"
        }
        
        # 메뉴 매핑
        self.menu_mapping = {
            "부대째": "부대찌개",
            "김치째개": "김치찌개",
            "불고기댐밥": "불고기덮밥",
            "불고기덜밥": "불고기덮밥",
            "불고 덮밥": "불고기덮밥",
            "불고기 덮밥": "불고기덮밥",
            "육회비범밥": "육회비빔밥",
            "제육뒷밥": "제육덮밥",
            "오징어뷰음": "오징어볶음",
            "골멩이비방면": "골뱅이비빔면"
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
            "Best", "Hot", "New", "Premium", "Special", "Deluxe", "Signature", "Chef's", "Real",
            "오늘의", "인기", "추천", "best", "new"
        ]

        
        logger.info("OCR 서비스 초기화 완료")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """이미지 전처리를 수행합니다 (기본 버전)."""
        try:
            # 1. 이미지 크기 조정 (너무 크면 조정)
            width, height = image.size
            if width > 2000 or height > 2000:
                # 너무 큰 이미지는 축소
                ratio = min(2000/width, 2000/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"이미지 크기 조정: {width}x{height} -> {new_width}x{new_height}")
            
            logger.info("이미지 전처리 완료 (기본 버전)")
            return image
            
        except Exception as e:
            logger.warning(f"이미지 전처리 중 오류 발생: {str(e)}")
            return image

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
        # 영어, 한글, 숫자, 공백만 남기고 제거
        text = re.sub(r'[^가-힣A-Za-z0-9\s]', ' ', text)
        
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 양쪽 공백 제거
        return text.strip().lower()  # 소문자로 변환

    def _is_menu_text(self, text: str) -> bool:
        """메뉴 텍스트인지 확인"""
        # 메뉴가 아닌 패턴 체크
        for pattern in self.non_menu_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        return True

    def _remove_modifiers(self, text: str) -> str:
        """수식어 제거"""
        for modifier in self.modifiers:
            text = re.sub(rf'\b{modifier}\b', '', text, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', text).strip()

    def _clean_and_normalize_text(self, text: str) -> str:
        """텍스트 정제 및 정규화"""
        try:
            # 기본 정제
            cleaned = text.strip()
            
            # 공백 정규화 (연속된 공백을 하나로)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            # OCR 오류 수정
            ocr_corrections = {
                "뷰음": "볶음",
                "째개": "찌개",
                "찌게": "찌개",
                "덜밥": "덮밥",
                "뒷밥": "덮밥",
                "비방": "비빔",
                "멩이": "뱅이",
                "콜면이": "골뱅이"
            }
            
            for error, correction in ocr_corrections.items():
                cleaned = cleaned.replace(error, correction)
            
            # 수량 정보 제거
            quantity_patterns = [
                r'\s*\(\s*\d+\s*인분?\s*\)\s*',  # (2인분)
                r'\s*\(\s*\d+\s*인이상\s*\)\s*',  # (2인이상)
                r'\s*\(\s*\d+\s*인\s*\)\s*',  # (2인)
                r'\s*\d+\s*인분\s*',  # 2인분
                r'\s*\d+\s*인이상\s*',  # 2인이상
                r'\s*\d+\s*인\s*',  # 2인
                r'\s*\(\s*추천\s*\d+\s*인분?\s*\)\s*',  # (추천2인분)
                r'\s*\(\s*추천\s*\d+\s*인\s*\)\s*'  # (추천2인)
            ]
            
            for pattern in quantity_patterns:
                cleaned = re.sub(pattern, '', cleaned)
            
            # 메뉴 단어 병합 패턴
            merge_patterns = {
                r'냉\s+면': '냉면',
                r'비빔\s+냉면': '비빔냉면',
                r'물\s+냉면': '물냉면',
                r'공\s+기\s+밥': '공기밥',
                r'김치\s+찌개': '김치찌개',
                r'된장\s+찌개': '된장찌개',
                r'순두부\s+찌개': '순두부찌개',
                r'부대\s+찌개': '부대찌개',
                r'오징어\s+볶음': '오징어볶음',
                r'돼지\s+김치찌개': '돼지김치찌개',
                r'참치\s+순두부찌개': '참치순두부찌개'
            }
            
            # 메뉴 단어 병합
            for pattern, replacement in merge_patterns.items():
                cleaned = re.sub(pattern, replacement, cleaned)
            
            # 불필요한 텍스트 제거 패턴
            remove_patterns = [
                r'\s*공기밥\s*별도\s*',
                r'\s*밥\s*별도\s*',
                r'\s*추가\s*',
                r'\s*선택\s*',
                r'\s*세트\s*',
                r'\s*포장\s*',
                r'\s*\(\s*공기밥\s*별도\s*\)\s*',
                r'\s*\(\s*밥\s*별도\s*\)\s*'
            ]
            
            # 불필요한 텍스트 제거
            for pattern in remove_patterns:
                cleaned = re.sub(pattern, '', cleaned)
            
            # 최종 공백 정리
            cleaned = cleaned.strip()
            
            # 디버깅을 위한 로그
            if cleaned != text:
                logger.debug(f"텍스트 정제: '{text}' -> '{cleaned}'")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"텍스트 정제 중 오류 발생: {str(e)}")
            return text

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

    def _calculate_hangul_similarity(self, text1: str, text2: str) -> float:
        """한글 자모 기반 유사도 계산"""
        try:
            # 한글 자모 분리
            decomposed1 = self._decompose_hangul(text1)
            decomposed2 = self._decompose_hangul(text2)
            
            # 자모 단위로 유사도 계산
            if not decomposed1 or not decomposed2:
                return 0.0
            
            # 자모 매칭 계산
            matches = 0
            total_chars = max(len(decomposed1), len(decomposed2))
            
            for i in range(min(len(decomposed1), len(decomposed2))):
                if decomposed1[i] == decomposed2[i]:
                    matches += 1
                # 유사한 자모에 대한 부분 점수
                elif self._is_similar_jamo(decomposed1[i], decomposed2[i]):
                    matches += 0.5
            
            return matches / total_chars if total_chars > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"한글 자모 유사도 계산 중 오류: {str(e)}")
            return 0.0

    def _is_similar_jamo(self, jamo1: str, jamo2: str) -> bool:
        """유사한 자모인지 확인"""
        similar_groups = [
            ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ'],  # 초성 유사 그룹
            ['ㅁ', 'ㅂ', 'ㅃ', 'ㅅ'],  # 초성 유사 그룹
            ['ㅇ', 'ㅈ', 'ㅉ', 'ㅊ'],  # 초성 유사 그룹
            ['ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'],  # 초성 유사 그룹
            ['ㅏ', 'ㅑ', 'ㅓ', 'ㅕ'],  # 중성 유사 그룹
            ['ㅗ', 'ㅛ', 'ㅜ', 'ㅠ'],  # 중성 유사 그룹
            ['ㅡ', 'ㅣ', 'ㅐ', 'ㅒ'],  # 중성 유사 그룹
            ['ㅔ', 'ㅖ', 'ㅘ', 'ㅙ'],  # 중성 유사 그룹
            ['ㅚ', 'ㅝ', 'ㅞ', 'ㅟ'],  # 중성 유사 그룹
            ['ㅢ', 'ㅚ', 'ㅟ', 'ㅡ'],  # 중성 유사 그룹
        ]
        
        for group in similar_groups:
            if jamo1 in group and jamo2 in group:
                return True
        return False

    def normalize_menu(self, text: str) -> str:
        """메뉴 이름을 정규화"""
        # # 영문 메뉴를 한글로 변환
        # if text.upper() in self.eng_to_kor:
        #     text = self.eng_to_kor[text.upper()]
        
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

    def extract_menu_from_text(self, text: str) -> Optional[str]:
        """텍스트에서 메뉴 이름 추출"""
        try:
            # 텍스트 전처리
            text = text.strip()
            if not text:
                return None

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

    def extract_menu_from_text_with_similarity(self, text: str) -> Optional[Tuple[str, float]]:
        """텍스트에서 메뉴 이름과 유사도를 함께 추출"""
        try:
            # 텍스트 전처리
            text = text.strip()
            if not text:
                return None

            # 영문 메뉴를 한글로 변환
            if text.upper() in self.eng_to_kor:
                return self.eng_to_kor[text.upper()], 1.0

            # 1단계: 기본 정규화
            normalized_text = self._normalize_text(text)
            if not normalized_text:
                return None
            
            # 2단계: 수식어 제거
            clean_text = self._remove_modifiers(normalized_text)
            if not clean_text:
                clean_text = normalized_text

            # # 3단계: 정확한 매칭 시도
            # exact_match = self._exact_match_exists(clean_text)
            # if exact_match:
            #     logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {exact_match} (정확히 일치)")
            #     return exact_match, 1.0

            # # 4단계: 포함된 메뉴 찾기
            # contained_menu = self._contains_menu(clean_text)
            # if contained_menu:
            #     logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {contained_menu} (부분 일치)")
            #     return contained_menu, 0.9

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

            return None

        except Exception as e:
            logger.error(f"메뉴 추출 중 오류 발생: {str(e)}")
            return None

    async def extract_text(self, image_bytes: bytes) -> List[dict]:
        """이미지에서 텍스트 추출"""
        try:
            # 이미지 바이트를 PIL Image로 변환
            image = Image.open(io.BytesIO(image_bytes))
            
            # 이미지 전처리
            processed_image = self._preprocess_image(image)
            
            # OCR 수행
            result = self.reader.readtext(np.array(processed_image))
            
            # 결과 정제
            extracted_texts = []
            logger.info(f"원본 이미지 OCR 결과 수: {len(result)}")
            
            for bbox, text, confidence in result:
                # bbox 좌표를 float로 변환
                bbox = [[float(coord) for coord in point] for point in bbox]
                
                # 텍스트 정제
                normalized = self._normalize_text(text)
                
                # 메뉴가 아닌 텍스트는 제외
                if not self._is_menu_text(normalized):
                    logger.info(f"메뉴가 아닌 텍스트로 제외: {text}")
                    continue
                
                # 정제된 텍스트
                cleaned = self._clean_and_normalize_text(text)
                
                if cleaned:  # 빈 문자열이 아닌 경우만 추가
                    # 최종 결과에서 수식어가 포함된 경우 다시 한 번 제거
                    final_text = self._remove_modifiers(cleaned)
                    if final_text:  # 수식어 제거 후에도 텍스트가 남아있는 경우만 추가
                        extracted_texts.append({
                            "text": final_text,
                            "confidence": confidence,
                            "bbox": bbox
                        })
                        logger.info(f"원본 텍스트: {text} -> 정제된 텍스트: {final_text} (신뢰도: {confidence:.2f})")
                    else:
                        logger.info(f"수식어 제거 후 빈 텍스트: {text}")
                else:
                    logger.info(f"제외된 텍스트: {text} (신뢰도: {confidence:.2f})")
            
            return extracted_texts
            
        except Exception as e:
            logger.error(f"텍스트 추출 중 오류 발생: {str(e)}")
            return []

    def process_image(self, image_data: bytes) -> List[str]:
        """이미지에서 메뉴 텍스트 추출"""
        try:
            # 이미지를 PIL Image로 변환
            image = Image.open(io.BytesIO(image_data))
            
            # 원본 이미지로 OCR 시도
            image_np = np.array(image)
            logger.info("원본 이미지로 OCR 시도")
            results = self.reader.readtext(image_np)
            logger.info(f"원본 이미지 OCR 결과 수: {len(results)}")
            
            # 추출된 텍스트 목록
            extracted_texts = []
            for bbox, text, conf in results:
                extracted_texts.append(text)
            
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

    def correct_with_levenshtein(self, text: str, cutoff: float = 0.8) -> Optional[str]:
        """
        정제된 텍스트가 메뉴와 유사하면 가장 가까운 메뉴로 교체
        이미 메뉴 사전에 있는 단어나 복합 메뉴는 교정하지 않음
        
        Args:
            text (str): 교정할 텍스트
            cutoff (float): 유사도 임계값 (0.0 ~ 1.0), 기본값 0.8로 상향 조정
        """
        if not text:
            return None
        
        # 텍스트가 너무 짧으면 교정하지 않음 (2글자 미만)
        if len(text.strip()) < 2:
            logger.info(f"텍스트가 너무 짧아 교정 제외: {text}")
            return text

        # 1. 전체 텍스트가 정확히 메뉴 사전에 있는 경우
        if text in self.menu_set:
            return text

        # 2. 복합 메뉴 처리 (예: "불고기 덮밥")
        words = text.split()
        if len(words) > 1:
            # 복합 메뉴의 각 부분이 메뉴 사전에 있는지 확인
            menu_parts = []
            for word in words:
                # 각 단어에 대해 유사도 검사 (단어가 2글자 이상인 경우만)
                if len(word) >= 2:
                    matches = get_close_matches(word, self.menu_set, n=1, cutoff=cutoff)
                    if matches:
                        menu_parts.append(matches[0])
                    else:
                        menu_parts.append(word)
                else:
                    menu_parts.append(word)
            
            corrected = ' '.join(menu_parts)
            if corrected != text:
                logger.info(f"부분 교정: {text} → {corrected} (유사도 임계값: {cutoff})")
            return corrected

        # 3. 단일 단어 메뉴 처리
        matches = get_close_matches(text, self.menu_set, n=1, cutoff=cutoff)
        if matches:
            best_match = matches[0]
            if best_match != text:
                # 유사도 계산 및 로깅
                similarity = SequenceMatcher(None, text, best_match).ratio()
                logger.info(f"레벤슈타인 교정: {text} → {best_match} (유사도: {similarity:.2f})")
            return best_match
        
        return text
