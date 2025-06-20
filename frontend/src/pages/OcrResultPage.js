import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import styles from '../styles/OcrResultPage.module.css';

const OcrResultPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // API 응답 구조에 맞게 데이터 처리
  const processResults = () => {
    const data = location.state?.results;
    console.log('받은 데이터:', data);  // 디버깅용 로그
    
    if (!data) return [];
    
    // found_foods 배열이 있으면 그것을 사용, 없으면 빈 배열 반환
    return data.found_foods || [];
  };

  const results = processResults();
  console.log('처리된 결과:', results);

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.backButton} onClick={handleBack}>
          <span>←</span>
        </button>
        <h1>분석 결과</h1>
      </div>

      <div className={styles.content}>
        <p className={styles.subtitle}>OCR로 인식된 음식 목록입니다</p>
        
        <div className={styles.resultList}>
          {Array.isArray(results) && results.length > 0 ? (
            results.map((item, index) => (
              <div key={index} className={styles.resultCard}>
                <div className={styles.locationIcon}>
                  <span className={styles.dot}></span>
                </div>
                <div className={styles.foodInfo}>
                  <h3 className={styles.foodName}>
                    {item.name || '알 수 없음'}
                  </h3>
                  <div className={styles.nutritionInfo}>
                    <span className={styles.calories}>
                      {item.nutrition_info?.calories || 0}
                    </span>
                    <span className={styles.unit}>kcal</span>
                    {item.nutrition_info?.nutrients && (
                      <div className={styles.nutrients}>
                        <span>탄수화물 {item.nutrition_info.nutrients.carbohydrates}g</span>
                        <span>단백질 {item.nutrition_info.nutrients.protein}g</span>
                        <span>지방 {item.nutrition_info.nutrients.fat}g</span>
                      </div>
                    )}
                  </div>
                </div>
                <button className={styles.detailButton}>
                  자세히 보기
                </button>
              </div>
            ))
          ) : (
            <div className={styles.emptyState}>
              <p>인식된 음식이 없습니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OcrResultPage; 