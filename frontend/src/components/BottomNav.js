import React from 'react';
import styles from '../styles/BottomNav.module.css';

const BottomNav = () => {
  const menuItems = [
    { icon: '📊', label: '대시보드' },
    { icon: '📝', label: '기록하기' },
    { icon: '📅', label: '캘린더' },
    { icon: '⚙️', label: '설정' },
  ];

  return (
    <nav className={styles.nav}>
      <div className={styles.header}>
        <h2>메뉴</h2>
      </div>
      <ul className={styles.menuList}>
        {menuItems.map((item) => (
          <li key={item.label} className={styles.menuItem}>
            <button className={styles.menuButton}>
              <span className={styles.icon}>{item.icon}</span>
              <span className={styles.label}>{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default BottomNav;
