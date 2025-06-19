// src/pages/MainPage.js
import React, { useState } from 'react';
import styles from '../styles/MainPage.module.css';
import MealCard from '../components/MealCard';
import SummaryCard from '../components/SummaryCard';
import BottomNav from '../components/BottomNav';

const MainPage = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  const meals = [
    {
      name: "아침",
      calories: 486,
      current: 0
    },
    {
      name: "점심",
      calories: 486,
      current: 0
    },
    {
      name: "저녁",
      calories: 486,
      current: 0
    }
  ];

  return (
    <div className={styles.mainPage}>
      {/* 메뉴 버튼 */}
      <button 
        className={styles.menuButton}
        onClick={() => setIsMenuOpen(!isMenuOpen)}
      >
        ☰
      </button>

      {/* 메뉴 사이드바 */}
      {isMenuOpen && (
        <div className={styles.sidebar}>
          <BottomNav />
        </div>
      )}

      {/* 메인 컨텐츠 */}
      <div className={styles.content}>
        <SummaryCard />
        <div className={styles.mealList}>
          {meals.map((meal, index) => (
            <MealCard key={meal.name} food={meal} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default MainPage;