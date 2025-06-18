import React from 'react';
import styles from '../styles/SummaryCard.module.css';

const SummaryCard = () => {
  const stats = [
    { label: '지방', value: '0' },
    { label: '단백질', value: '0' },
    { label: '탄수화물', value: '0' },
    { label: '섭취량', value: '0' },
  ];

  return (
    <div className={styles.summaryWrapper}>
      <div className={styles.topBackground}></div>
      <div className={styles.summaryCard}>
        <div className={styles.header}>
          <div className={styles.kcalCircle}>
            <span className={styles.kcalValue}>0</span>
            <span className={styles.kcalLabel}>kcal 남음</span>
          </div>
          <div className={styles.statsGrid}>
            {stats.map((stat, index) => (
              <div key={index} className={styles.statItem}>
                <span className={styles.statValue}>{stat.value}</span>
                <span className={styles.statLabel}>{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;

