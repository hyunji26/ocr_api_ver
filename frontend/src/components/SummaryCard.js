import React from 'react';
import styles from '../styles/MainPage.module.css';

export default function SummaryCard() {
  // 더미 데이터
  const remainKcal = 0;
  const consumed = 0;
  const burned = 0;
  const nutrients = [
    { label: '탄수화물', value: 0 },
    { label: '단백질', value: 0 },
    { label: '지방', value: 0 },
    { label: '섬유질', value: 0 },
  ];

  return (
    <section className={styles.summaryCard}>
      <div className={styles.summaryTop}>
        <div className={styles.summaryRemain}>
          <div className={styles.kcalCircle}>
            <span className={styles.kcalValue}>{remainKcal}</span>
            <span className={styles.kcalUnit}>kcal</span>
            {/* <span className={styles.kcalLabel}>남음음</span> */}
          </div>
        </div>
        <div className={styles.summaryProfile}>
          <div className={styles.profileCircle} />
        </div>
      </div>
      <div className={styles.summaryStats}>
      </div>
      <div className={styles.nutrientBar}>
        {nutrients.map(n => (
          <div key={n.label} className={styles.nutrientItem}>
            <span className={styles.nutrientLabel}>{n.label}</span>
            <span className={styles.nutrientValue}>{n.value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

