// src/pages/MainPage.js
import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';
import MainAlert from '../components/MainAlert';
import { useMeal } from '../context/MealContext';

// API 기본 URL 설정
const API_BASE_URL = `http://${window.location.hostname}:8000`;  // 현재 호스트 주소 사용

console.log('Current hostname:', window.location.hostname);
console.log('API Base URL:', API_BASE_URL);

const MainPage = () => {
  const [loading, setLoading] = useState({
    breakfast: false,
    lunch: false,
    dinner: false
  });
  const [nutritionStats, setNutritionStats] = useState({
    balance_score: null,
    total_calories: null,
    daily_calorie_goal: 2000,
    highlight: '',
    needs_improvement: '',
    last_meal_time: '0시간 전',
    nutrients: {
      carbohydrates: null,
      protein: null,
      fat: null
    },
    meal_calories: {
      breakfast: null,
      lunch: null,
      dinner: null
    }
  });
  const [showAlert, setShowAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertType, setAlertType] = useState('success');

  const fileInputRefs = {
    breakfast: useRef(null),
    lunch: useRef(null),
    dinner: useRef(null)
  };
  const navigate = useNavigate();
  const { shouldRefresh } = useMeal();

  // API에서 영양 정보 가져오기
  useEffect(() => {
    const fetchNutritionStats = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // 영양 통계 정보 가져오기
        const statsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/stats`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!statsResponse.ok) {
          // 토큰이 만료된 경우
          if (statsResponse.status === 401) {
            // 새로운 토큰 발급
            const tokenResponse = await fetch(`${API_BASE_URL}/api/v1/balance/token`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              }
            });
            
            if (tokenResponse.ok) {
              const data = await tokenResponse.json();
              localStorage.setItem('token', data.access_token);
              // 새로운 토큰으로 재시도
              return fetchNutritionStats();
            } else {
              navigate('/login');
              return;
            }
          }
          throw new Error(`Stats API Error: ${statsResponse.status}`);
        }
        
        const statsData = await statsResponse.json();
        console.log('Stats API Response:', statsData);

        // 식사별 칼로리 정보 가져오기
        const mealsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/meals`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!mealsResponse.ok) {
          throw new Error(`Meals API Error: ${mealsResponse.status}`);
        }

        const mealCalories = await mealsResponse.json();
        console.log('Meals API Response:', mealCalories);

        // 각 식사 타입별 칼로리 합계 계산
        const breakfast_calories = mealCalories.breakfast?.reduce((sum, meal) => sum + meal.calories, 0) || 0;
        const lunch_calories = mealCalories.lunch?.reduce((sum, meal) => sum + meal.calories, 0) || 0;
        const dinner_calories = mealCalories.dinner?.reduce((sum, meal) => sum + meal.calories, 0) || 0;

        setNutritionStats(prev => ({
          ...statsData,
          meal_calories: {
            breakfast: breakfast_calories,
            lunch: lunch_calories,
            dinner: dinner_calories
          }
        }));
      } catch (error) {
        console.error('영양 정보 조회 중 오류 발생:', error);
      }
    };

    fetchNutritionStats();
  }, [navigate, shouldRefresh]);

  useEffect(() => {
    let timeoutId;
    if (showAlert) {
      timeoutId = setTimeout(() => {
        setShowAlert(false);
      }, 2000);
    }
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [showAlert]);

  const getHealthMessage = (percentage) => {
    if (percentage === 0) {
      return "오늘의 첫 식사를 기록해보세요! 🌱";
    }else if (percentage < 70) {
      return "아직 여유가 있어요!🍽️";
    } else if (percentage < 100) {
      return "권장 칼로리에 거의 다달았어요! 👏";
    } else if (percentage === 100) {
      return "하루 권장 칼로리에 도달했어요! 💪";
    } else{
      return "내일을 위해 조절해보세요💪";
    }
  };

  const handleCapture = async (file, mealType) => {
    try {
      setLoading(prev => ({ ...prev, [mealType]: true }));
      console.log('파일 선택됨:', file.name);

      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const formData = new FormData();
      formData.append('file', file);

      console.log('API 호출 시작...');
      
      // OCR 결과 페이지로 먼저 이동
      navigate('/ocr-result', { 
        state: { 
          mealType,
          isProcessing: true
        } 
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/food/analyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          navigate('/login');
          return;
        }
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      console.log('API 응답 결과:', data);
      
      navigate('/ocr-result', { 
        state: { 
          results: data, 
          mealType,
          isProcessing: false 
        },
        replace: true
      });

    } catch (error) {
      console.error('API 호출 중 에러 발생:', error);
      setAlertMessage('이미지 분석 중 오류가 발생했습니다.');
      setAlertType('error');
      setShowAlert(true);
      navigate(-1);
    } finally {
      setLoading(prev => ({ ...prev, [mealType]: false }));
    }
  };

  const handleFileSelect = (event, mealType) => {
    const file = event.target.files[0];
    if (file) {
      handleCapture(file, mealType);
    }
  };

  const openFileInput = (mealType) => {
    fileInputRefs[mealType].current.click();
  };

  // 칼로리 달성률 계산
  const percentage = nutritionStats.daily_calorie_goal 
    ? Math.round((nutritionStats.total_calories / nutritionStats.daily_calorie_goal) * 100) || 0
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 font-sans relative pb-[72px]">
      <div className="max-w-lg mx-auto bg-transparent px-6 pb-24 overflow-y-auto">

        {/* Header Section */}
        <header className="pt-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">NutriScan</h1>
          </div>
          <div 
            onClick={() => navigate('/profile')}
            className="w-10 h-10 bg-white rounded-full flex items-center justify-center cursor-pointer"
          >
            <i className="fas fa-user text-gray-600"></i>
          </div>
        </header>

        {/* Balance & Expenses Summary */}
        <div className="mt-6">
          <div className="flex justify-between mb-2">
            <div>
              <p className="text-xs text-gray-700">오늘의 총 칼로리</p>
              <h2 className="text-2xl font-bold text-gray-800">{(nutritionStats?.total_calories || 0).toLocaleString()} kcal</h2>
              <p className="text-xs text-blue-500 mt-1">{getHealthMessage(percentage)}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-700">하루 권장 칼로리</p>
              <h2 className="text-2xl font-bold text-blue-500">{(nutritionStats?.daily_calorie_goal || 0).toLocaleString()} kcal</h2>
              <p className="text-xs text-gray-600 mt-1">{percentage}% 달성중</p>
            </div>
          </div>
          
          {/* 새로운 식사 밸런스 스코어 카드 */}
          <div className="bg-white bg-opacity-20 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center">
                  <span className="text-xl font-bold text-blue-500">{nutritionStats.balance_score || 0}</span>
                </div>
                <div className="ml-3">
                  <h3 className="font-medium text-gray-800">오늘의 밸런스</h3>
                  <p className="text-xs text-gray-500">오늘도 건강한 식사 하세요 🔥</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center text-sm">
                <i className="fas fa-arrow-trend-up text-emerald-500 mr-2"></i>
                <span className="text-gray-600">오늘의 베스트: </span>
                <span className="ml-1 font-medium text-emerald-600">
                  {nutritionStats?.highlight ? `${nutritionStats.highlight} 섭취가 훌륭해요!` : '오늘의 식사를 기록해 보세요!'}
                </span>
              </div>
              <div className="flex items-center text-sm">
                <i className="fas fa-lightbulb text-amber-500 mr-2"></i>
                <span className="text-gray-600">내일의 도전: </span>
                <span className="ml-1 font-medium text-amber-600">
                  {nutritionStats?.needs_improvement ? `${nutritionStats.needs_improvement} 균형을 맞춰보세요` : '오늘의 식사를 기록해 보세요!'}
                </span>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-8">
            <div className="w-full bg-white bg-opacity-50 rounded-full h-2.5">
              <div 
                className="bg-emerald-500 h-2.5 rounded-full transition-all duration-500 ease-in-out" 
                style={{ width: `${Math.min(percentage, 100)}%` }}
              >
              </div>
            </div>
            <div className="mt-2 flex justify-between text-xs text-gray-600">
              <span>{nutritionStats.total_calories || 0} kcal</span>
              <span>{nutritionStats.daily_calorie_goal || 2000} kcal</span>
            </div>
          </div>
        </div>

        {/* Meal List */}
        <div className="mt-8">
          <div className="space-y-4">
            {/* Breakfast */}
            <div className="bg-white rounded-xl p-4 flex items-center">
              <input
                type="file"
                ref={fileInputRefs.breakfast}
                onChange={(e) => handleFileSelect(e, 'breakfast')}
                accept="image/*"
                className="hidden"
              />
              <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
                <i className="fas fa-sun text-blue-400"></i>
              </div>
              <div className="ml-3 flex-1">
                <div className="flex justify-between">
                  <h3 className="font-medium text-gray-800">아침</h3>
                  <span className="font-bold text-gray-800">
                    {Math.round(nutritionStats.meal_calories.breakfast)} kcal
                  </span>
                </div>
                <div className="flex justify-between mt-1">
                  <p className="text-xs text-gray-500">식사를 기록해 보세요</p>
                  <button 
                    onClick={() => openFileInput('breakfast')}
                    disabled={loading.breakfast}
                    className="text-xs px-3 py-1 rounded-full bg-blue-50 text-blue-500 hover:bg-blue-100 transition-colors flex items-center gap-1"
                  >
                    {loading.breakfast ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <>
                        <i className="fas fa-plus text-xs"></i>
                        <span>추가</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Lunch */}
            <div className="bg-white rounded-xl p-4 flex items-center">
              <input
                type="file"
                ref={fileInputRefs.lunch}
                onChange={(e) => handleFileSelect(e, 'lunch')}
                accept="image/*"
                className="hidden"
              />
              <div className="w-10 h-10 bg-indigo-50 rounded-full flex items-center justify-center">
                <i className="fas fa-utensils text-indigo-400"></i>
              </div>
              <div className="ml-3 flex-1">
                <div className="flex justify-between">
                  <h3 className="font-medium text-gray-800">점심</h3>
                  <span className="font-bold text-gray-800">
                    {Math.round(nutritionStats.meal_calories.lunch)} kcal
                  </span>
                </div>
                <div className="flex justify-between mt-1">
                  <p className="text-xs text-gray-500">식사를 기록해 보세요</p>
                  <button 
                    onClick={() => openFileInput('lunch')}
                    disabled={loading.lunch}
                    className="text-xs px-3 py-1 rounded-full bg-indigo-50 text-indigo-500 hover:bg-indigo-100 transition-colors flex items-center gap-1"
                  >
                    {loading.lunch ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <>
                        <i className="fas fa-plus text-xs"></i>
                        <span>추가</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Dinner */}
            <div className="bg-white rounded-xl p-4 flex items-center">
              <input
                type="file"
                ref={fileInputRefs.dinner}
                onChange={(e) => handleFileSelect(e, 'dinner')}
                accept="image/*"
                className="hidden"
              />
              <div className="w-10 h-10 bg-purple-50 rounded-full flex items-center justify-center">
                <i className="fas fa-moon text-purple-400"></i>
              </div>
              <div className="ml-3 flex-1">
                <div className="flex justify-between">
                  <h3 className="font-medium text-gray-800">저녁</h3>
                  <span className="font-bold text-gray-800">
                    {Math.round(nutritionStats.meal_calories.dinner)} kcal
                  </span>
                </div>
                <div className="flex justify-between mt-1">
                  <p className="text-xs text-gray-500">식사를 기록해 보세요</p>
                  <button 
                    onClick={() => openFileInput('dinner')}
                    disabled={loading.dinner}
                    className="text-xs px-3 py-1 rounded-full bg-purple-50 text-purple-500 hover:bg-purple-100 transition-colors flex items-center gap-1"
                  >
                    {loading.dinner ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <>
                        <i className="fas fa-plus text-xs"></i>
                        <span>추가</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Navigation */}
        <BottomNav />
      </div>
    </div>
  );
};

export default MainPage;