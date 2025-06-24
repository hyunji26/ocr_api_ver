import React, { useState, useEffect } from 'react';

const LoadingSpinner = () => {
  const [loadingText, setLoadingText] = useState('맛있는 식사를 기록하는 중');
  const [dots, setDots] = useState('');

  const loadingMessages = [
    "영양 정보를 분석하고 있어요",
    "건강한 식사 기록 중입니다",
    "맛있는 식사를 기록하는 중",
    "오늘도 건강한 하루 되세요",
    "식사 기록을 저장하고 있어요"
  ];

  useEffect(() => {
    // 로딩 메시지 자동 변경
    const messageInterval = setInterval(() => {
      setLoadingText(prev => {
        const currentIndex = loadingMessages.indexOf(prev);
        return loadingMessages[(currentIndex + 1) % loadingMessages.length];
      });
    }, 2000);

    // 점 애니메이션
    const dotsInterval = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);

    return () => {
      clearInterval(messageInterval);
      clearInterval(dotsInterval);
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4 shadow-xl">
        <div className="flex flex-col items-center">
          {/* 접시 아이콘 애니메이션 */}
          <div className="relative w-20 h-20 mb-6">
            <div className="absolute inset-0 flex items-center justify-center animate-bounce">
              <i className="fas fa-utensils text-4xl text-emerald-500"></i>
            </div>
          </div>
          
          {/* 로딩 메시지 */}
          <p className="text-gray-700 text-lg font-medium text-center mb-2">
            {loadingText}{dots}
          </p>
          
          {/* 프로그레스 바 */}
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mt-4">
            <div className="h-full bg-emerald-500 animate-loading-progress"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner; 