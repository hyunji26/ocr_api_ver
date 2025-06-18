// src/pages/MainPage.js
import React, { useState } from 'react';
import styles from '../styles/MainPage.module.css';
import MealCard from '../components/MealCard';
import SummaryCard from '../components/SummaryCard';
import BottomNav from '../components/BottomNav';

const MainPage = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

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
          <MealCard title="아침" targetKcal={486} />
          <MealCard title="점심" targetKcal={486} />
          <MealCard title="저녁" targetKcal={486} />
        </div>
      </div>
    </div>
  );
};

export default MainPage;