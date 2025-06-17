// src/pages/MainPage.js
import React from 'react';
import SummaryCard from '../components/SummaryCard';
import MealCard from '../components/MealCard';
// import CuteCharacter from '../components/CuteCharacter';
import BottomNav from '../components/BottomNav';
import styles from '../styles/MainPage.module.css';

const foodList = [
  { name: '아침', calories: 486 },
  { name: '점심', calories: 486 },
  { name: '저녁', calories: 486 },
  { name: '간식', calories: 162 }
];

const MainPage = () => {
  return (
    <div className={styles.mainPage}>
      <SummaryCard />
      <div className={styles.mealList}>
        {foodList.map((food) => (
          <MealCard key={food.name} food={food} />
        ))}
      </div>
      <BottomNav />
    </div>
  );
};

export default MainPage;