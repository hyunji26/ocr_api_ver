import React, { useRef, useState } from 'react';
import styles from '../styles/MealCard.module.css';

const MealCard = ({ food }) => {
  const { name, calories } = food;
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  // 식사 시간대별 이모지 매핑
  const mealEmoji = {
    아침: '☀️',
    점심: '⛅',
    저녁: '🌃',
    간식: '🌭'
  };

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
      
      // 세부 정보 로깅
      if (data.text) {
        console.log('추출된 텍스트:', data.text);
      }
      if (data.calories) {
        console.log('칼로리:', data.calories);
      }
      if (data.nutrients) {
        console.log('영양소 정보:', data.nutrients);
      }
      if (data.error) {
        console.error('에러 발생:', data.error);
      }

    } catch (error) {
      console.error('API 호출 중 에러 발생:', error);
      alert('이미지 분석 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    console.log('파일 선택 이벤트 발생');
    const file = event.target.files[0];
    if (file) {
      console.log('선택된 파일 정보:', {
        이름: file.name,
        크기: file.size + ' bytes',
        타입: file.type
      });
      handleCapture(file);
    } else {
      console.log('파일이 선택되지 않음');
    }
  };

  const openCamera = () => {
    console.log('=== 디버깅 시작 ===');
    console.log('버튼 클릭됨');
    console.log('fileInputRef:', fileInputRef.current);
    fileInputRef.current.click();
  };
  
  return (
    <div className={styles.mealCard}>
      <div className={styles.mealEmoji}>
        {mealEmoji[name]}
      </div>
      <div className={styles.foodInfo}>
        <div>
          <h3 className={styles.foodName}>{name}</h3>
          <p className={styles.calories}>0 / {calories} kcal</p>
        </div>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileSelect}
          ref={fileInputRef}
          style={{ display: 'none' }}
        />
        <button 
          className={styles.addButton}
          onClick={openCamera}
          disabled={loading}
        >
          {loading ? '...' : '+'}
        </button>
      </div>
    </div>
  );
};

export default MealCard;

