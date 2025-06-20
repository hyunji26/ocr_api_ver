import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/MealCard.module.css';

const MealCard = ({ food }) => {
  const { name, calories, current } = food;
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleCapture = async (file) => {
    try {
      setLoading(true);
      console.log('파일 선택됨:', file.name);

      const formData = new FormData();
      formData.append('file', file);

      console.log('API 호출 시작...');
      const response = await fetch('http://localhost:8000/api/v1/food/analyze', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
      });

      const data = await response.json();
      console.log('API 응답 결과:', data);
      
      // 결과 페이지로 이동
      navigate('/result', { state: { results: data } });

    } catch (error) {
      console.error('API 호출 중 에러 발생:', error);
      alert('이미지 분석 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleCapture(file);
    }
  };

  const openCamera = () => {
    fileInputRef.current.click();
  };

  return (
    <div className={styles.mealCard}>
      <div className={styles.mealInfo}>
        <h2 className={styles.title}>{name}</h2>
        <p className={styles.subtitle}>목표 {calories}kcal | 현재 {current}kcal</p>
      </div>
      
      <div className={styles.playInfo}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*"
          capture="environment"
          style={{ display: 'none' }}
        />
        <button 
          className={styles.fabButton} 
          onClick={openCamera}
          disabled={loading}
        >
          {loading ? (
            <div className={styles.loadingSpinner}></div>
          ) : (
            <span className={styles.fabIcon}>+</span>
          )}
        </button>
      </div>
    </div>
  );
};

export default MealCard;

