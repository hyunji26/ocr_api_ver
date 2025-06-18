import React, { useState } from 'react';
import styles from '../styles/MealCard.module.css';

const MealCard = ({ title, targetKcal }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleImageCapture = () => {
    setIsLoading(true);
    // 이미지 캡처 로직
    setTimeout(() => {
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className={styles.mealCardContainer}>
      <div className={styles.mealCard}>
        <div className={styles.mealInfo}>
          <h2 className={styles.title}>{title}</h2>
          <p className={styles.subtitle}>오늘의 식사를 기록해보세요</p>
          <div className={styles.calorieInfo}>
            <span className={styles.currentCalories}>0</span>
            <span className={styles.separator}>/</span>
            <span className={styles.targetCalories}>{targetKcal}</span>
            <span className={styles.unit}>kcal</span>
          </div>
        </div>
        <button 
          className={styles.captureButton}
          onClick={handleImageCapture}
          disabled={isLoading}
        >
          {isLoading ? '...' : '+'}
        </button>
      </div>
    </div>
  );
};

export default MealCard;

