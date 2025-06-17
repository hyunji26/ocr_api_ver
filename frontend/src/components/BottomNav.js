import React from "react";
import styles from "../styles/BottomNav.module.css";

const BottomNav = () => {
  return (
    <nav className={styles.bottomNav}>
      <button className={styles.navItem}>
        <span role="img" aria-label="코치">🏠</span>
        <span>코치</span>
      </button>
      <button className={styles.navItem}>
        <span role="img" aria-label="일지">📋</span>
        <span>일지</span>
      </button>
      <button className={styles.navItem}>
        <span role="img" aria-label="프로필">👤</span>
        <span>프로필</span>
      </button>
    </nav>
  );
};

export default BottomNav;
