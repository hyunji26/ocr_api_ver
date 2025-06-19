import pandas as pd
import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class MenuDictGenerator:
    _instance = None
    _menu_dict = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MenuDictGenerator, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._menu_dict = None
    
    def get_menu_dict(self, csv_path: str) -> Set[str]:
        """메뉴 목록을 가져옴 (없으면 생성)"""
        if self._menu_dict is None:
            self._menu_dict = self._generate_menu_dict(csv_path)
        return self._menu_dict
    
    def _generate_menu_dict(self, csv_path: str) -> Set[str]:
        """CSV 파일에서 메뉴 목록을 생성"""
        try:
            logger.info("[DEBUG] CSV 읽기 시작")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info("[DEBUG] CSV 읽기 완료")
            
            logger.info("[DEBUG] 메뉴 이름 추출 시작")
            # '식품명' 열에서 메뉴 이름만 추출 + 중복 제거
            menu_set = set(df['식품명'].dropna().unique())
            logger.info(f"[DEBUG] 메뉴 이름 추출 완료: {len(menu_set)}개")
            
            # 기본 메뉴명 추가
            basic_menus = self._extract_basic_menus(menu_set)
            menu_set.update(basic_menus)
            logger.info(f"[DEBUG] 기본 메뉴명 추가 완료: {len(menu_set)}개")
            
            return menu_set
            
        except Exception as e:
            logger.error(f"메뉴 목록 생성 중 오류 발생: {str(e)}")
            # 기본 메뉴 목록 반환
            return {
                "비빔밥",
                "김치찌개",
                "된장찌개",
                "갈비탕",
                "만두국",
                "돈까스",
                "치킨가라아게",
                "소세지"
            }
    
    def _extract_basic_menus(self, menu_set: Set[str]) -> Set[str]:
        """복합 메뉴명에서 기본 메뉴명을 추출"""
        basic_menus = set()
        
        # 기본 메뉴명 패턴
        basic_patterns = [
            "돈까스", "치킨가라아게", "소세지", "피자", "햄버거", "샌드위치",
            "김치찌개", "된장찌개", "갈비탕", "만두국", "비빔밥", "불고기",
            "닭볶음탕", "해물탕", "감자튀김", "치킨", "스테이크", "파스타"
        ]
        
        for menu in menu_set:
            for pattern in basic_patterns:
                if pattern in menu:
                    basic_menus.add(pattern)
        
        return basic_menus

# 전역 인스턴스 생성
menu_dict_generator = MenuDictGenerator()

def get_menu_dict(csv_path: str) -> Set[str]:
    """메뉴 목록을 가져오는 편의 함수"""
    return menu_dict_generator.get_menu_dict(csv_path) 