import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import BottomNav from '../components/BottomNav';
import LoadingSpinner from '../components/LoadingSpinner';
import SaveAlert from '../components/SaveAlert';
import { useMeal } from '../context/MealContext';

// API 기본 URL 설정
const API_BASE_URL = `http://${window.location.hostname}:8000`;  // 현재 호스트 주소 사용

console.log('Current hostname:', window.location.hostname);
console.log('API Base URL:', API_BASE_URL);

const MealCard = ({ food }) => (
  <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
    <div className="flex justify-between items-start mb-3">
      <div>
        <h3 className="text-xl font-semibold text-gray-800">{food.name}</h3>
        <div className="text-sm font-medium text-gray-600 mt-1">{food.calories} kcal</div>
      </div>
    </div>
    <div className="flex justify-between items-center mt-4">
      <div className="flex justify-between w-full max-w-xs">
        <div className="flex flex-col items-center px-4 border-r border-gray-200">
          <div className="text-xs font-medium text-gray-500">탄수화물</div>
          <div className="mt-1 text-sm font-semibold text-emerald-600">{food.nutrients.carbohydrates}g</div>
        </div>
        <div className="flex flex-col items-center px-4 border-r border-gray-200">
          <div className="text-xs font-medium text-gray-500">단백질</div>
          <div className="mt-1 text-sm font-semibold text-emerald-600">{food.nutrients.protein}g</div>
        </div>
        <div className="flex flex-col items-center px-4">
          <div className="text-xs font-medium text-gray-500">지방</div>
          <div className="mt-1 text-sm font-semibold text-emerald-600">{food.nutrients.fat}g</div>
        </div>
      </div>
    </div>
  </div>
);

const OcrResultPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { triggerRefresh } = useMeal();
  const [activeTab, setActiveTab] = useState(1);
  const [selectedFoods, setSelectedFoods] = useState(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [showSaveAlert, setShowSaveAlert] = useState(false);
  const [loadingMessages] = useState([
    "음식을 인식하고 있어요...",
    "영양 정보를 분석 중이에요..."
  ]);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [existingStats, setExistingStats] = useState({
    total_calories: 0,
    nutrients: {
      carbohydrates: 0,
      protein: 0,
      fat: 0
    },
    meal_calories: []
  });
  
  // 전달받은 날짜가 있으면 사용, 없으면 현재 날짜 사용
  const [selectedDate, setSelectedDate] = useState(
    location.state?.selectedDate || new Date().toISOString().split('T')[0]
  );
  
  const [selectedTime, setSelectedTime] = useState(
    new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
  );

  const fetchBalanceStats = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/balance/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        
        // 식사별 칼로리 정보도 함께 가져오기
        const mealsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/meals`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const mealCalories = await mealsResponse.json();
        
        setExistingStats({
          total_calories: data.total_calories || 0,
          nutrients: {
            carbohydrates: data.nutrients?.carbohydrates || 0,
            protein: data.nutrients?.protein || 0,
            fat: data.nutrients?.fat || 0
          },
          meal_calories: mealCalories  // 식사별 칼로리 정보 추가
        });
      }
    } catch (error) {
      console.error('Failed to fetch balance stats:', error);
    }
  };
  
  useEffect(() => {
    fetchBalanceStats();
  }, []);

  useEffect(() => {
    let intervalId;
    if (location.state?.isProcessing) {
      intervalId = setInterval(() => {
        setCurrentMessageIndex(prev => (prev + 1) % loadingMessages.length);
      }, 4000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [location.state?.isProcessing, loadingMessages.length]);

  useEffect(() => {
    let timeoutId;
    if (showSaveAlert) {
      timeoutId = setTimeout(() => {
        setShowSaveAlert(false);
        navigate('/');
      }, 1500);
    }
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [showSaveAlert, navigate]);

  const processResults = () => {
    const data = location.state?.results;
    if (!data) return [];
    // 영양 정보가 있는 메뉴만 필터링 (calories가 0인 경우는 영양 정보가 없는 경우)
    return Array.isArray(data) ? data.filter(item => item.calories > 0) : [];
  };

  const results = processResults();
  const mealType = location.state?.mealType || 'breakfast';

  const formatNumber = (num) => {
    if (num === undefined || num === null) return '0';
    const number = parseFloat(num);
    return isNaN(number) ? '0' : number.toFixed(1);
  };

  const getTotalNutrition = () => {
    const selectedNutrition = results.reduce((acc, item) => {
      if (!selectedFoods.has(item.name)) return acc;
      const nutrition = item.nutrition_info || item; // nutrition_info가 없으면 item 자체를 사용
      const nutrients = nutrition.nutrients || {};
      return {
        calories: parseFloat(acc.calories || 0) + parseFloat(nutrition.calories || 0),
        carbohydrates: parseFloat(acc.carbohydrates || 0) + parseFloat(nutrients.carbohydrates || 0),
        protein: parseFloat(acc.protein || 0) + parseFloat(nutrients.protein || 0),
        fat: parseFloat(acc.fat || 0) + parseFloat(nutrients.fat || 0)
      };
    }, { calories: 0, carbohydrates: 0, protein: 0, fat: 0 });

    // 기존 영양 정보와 합산
    return {
      calories: selectedNutrition.calories + existingStats.total_calories,
      carbohydrates: selectedNutrition.carbohydrates + existingStats.nutrients.carbohydrates,
      protein: selectedNutrition.protein + existingStats.nutrients.protein,
      fat: selectedNutrition.fat + existingStats.nutrients.fat
    };
  };

  const totalNutrition = getTotalNutrition();
  const totalCalories = 2000;
  const caloriePercentage = Math.round((totalNutrition.calories / totalCalories) * 100) || 0;

  const handleFoodSelect = (foodName) => {
    const newSelected = new Set(selectedFoods);
    if (newSelected.has(foodName)) {
      newSelected.delete(foodName);
    } else {
      newSelected.add(foodName);
    }
    setSelectedFoods(newSelected);
  };

  const saveMeals = async () => {
    if (selectedFoods.size === 0) {
      alert('선택된 음식이 없습니다.');
      return;
    }

    setIsSaving(true);
    try {
      const selectedItems = results.filter(item => selectedFoods.has(item.name));
      
      for (const item of selectedItems) {
        // 선택한 날짜와 시간으로 timestamp 생성
        const [year, month, day] = selectedDate.split('-');
        const [hours, minutes] = selectedTime.split(':');
        const timestamp = new Date(
          parseInt(year),
          parseInt(month) - 1,
          parseInt(day),
          parseInt(hours),
          parseInt(minutes)
        ).toISOString();

        const mealData = {
          meal_type: mealType.toLowerCase(),
          food_name: item.name,
          calories: parseFloat(item.calories || 0),
          carbohydrates: parseFloat(item.nutrients?.carbohydrates || 0),
          protein: parseFloat(item.nutrients?.protein || 0),
          fat: parseFloat(item.nutrients?.fat || 0),
          timestamp: timestamp
        };

        const response = await fetch('/api/v1/meals', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(mealData)
        });

        if (!response.ok) {
          throw new Error('Failed to save meal');
        }
      }

      setShowSaveAlert(true);
      triggerRefresh();
      
      // 저장 완료 후 이전 페이지로 돌아가기
      setTimeout(() => {
        navigate(location.state?.returnPath || '/meal-log');
      }, 1500);
    } catch (error) {
      console.error('Error saving meals:', error);
      alert('식사 저장 중 오류가 발생했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 font-sans relative pb-[72px]">
      {showSaveAlert && <SaveAlert />}
      {(isSaving || location.state?.isProcessing) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex flex-col items-center justify-center">
          <LoadingSpinner />
          <p className="text-white mt-4 text-lg font-medium">
            {isSaving ? '저장 중...' : loadingMessages[currentMessageIndex]}
          </p>
        </div>
      )}
      
      {location.state?.isProcessing ? (
        <div className="flex flex-col items-center justify-center h-screen">
          <div className="text-white text-center p-6">
            <h1 className="text-2xl font-bold mb-4">음식 분석 중</h1>
            <p className="text-lg opacity-90">{loadingMessages[currentMessageIndex]}</p>
          </div>
        </div>
      ) : (
        <>
          {/* Header Area */}
          <div className="p-6 text-white">
            <div className="flex items-center gap-4 mb-4">
              <button onClick={() => navigate(-1)} className="text-2xl">
                <i className="fas fa-arrow-left"></i>
              </button>
              <div className="flex items-center gap-2">
                <i className="fas fa-utensils text-xl"></i>
                <span className="text-xl">{mealType}</span>
              </div>
              <button 
                onClick={saveMeals}
                disabled={isSaving || selectedFoods.size === 0}
                className={`ml-auto px-4 py-2 rounded-full text-sm font-medium transition-all
                  ${selectedFoods.size > 0 
                    ? 'bg-white text-emerald-500 hover:bg-emerald-50' 
                    : 'bg-white/50 text-white/50 cursor-not-allowed'}`}
              >
                {isSaving ? '저장 중...' : `${selectedFoods.size}개 저장`}
              </button>
            </div>

            <div className="mb-6">
              <h1 className="text-4xl font-bold mb-2">
                {Math.round(totalNutrition.calories).toLocaleString()} kcal
              </h1>
              <div className="flex items-center gap-2 text-sm opacity-90">
                <span>{caloriePercentage}%</span>
                <div className="flex-1 h-1 bg-white bg-opacity-30 rounded-full">
                  <div 
                    className="h-full bg-white rounded-full transition-all" 
                    style={{ width: `${Math.min(caloriePercentage, 100)}%` }}
                  ></div>
                </div>
              </div>
              <p className="text-sm mt-2 flex items-center gap-2">
                <i className="fas fa-circle-check"></i>
                <span>
                  {selectedFoods.size > 0 
                    ? `이 메뉴들로 하루 권장량의 ${caloriePercentage}%를 채울 수 있어요.`
                    : '음식을 선택해주세요.'}
                </span>
              </p>
            </div>

            <div className="text-sm opacity-90">
              <div className="flex items-center gap-1">
                <span>탄 {formatNumber(totalNutrition.carbohydrates)}g</span>
                <span>•</span>
                <span>단 {formatNumber(totalNutrition.protein)}g</span>
                <span>•</span>
                <span>지 {formatNumber(totalNutrition.fat)}g</span>
              </div>
            </div>
          </div>

          {/* Food List */}
          <div className="flex-1 bg-[#F1FFF3] rounded-t-[2rem] p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-800">
                인식된 음식 목록
                <span className="ml-2 text-sm text-gray-500">총 {results.length}개</span>
              </h2>
            </div>

            <div className="space-y-4">
              {results.length > 0 ? (
                results.map((item, index) => (
                  <div 
                    key={index} 
                    className={`bg-white rounded-2xl p-4 shadow-sm transition-all cursor-pointer
                      ${selectedFoods.has(item.name) 
                        ? 'ring-2 ring-emerald-500 shadow-emerald-100' 
                        : 'hover:shadow-md'}`}
                    onClick={() => handleFoodSelect(item.name)}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`rounded-full p-3 transition-colors
                        ${selectedFoods.has(item.name) 
                          ? 'bg-emerald-500' 
                          : 'bg-emerald-100'}`}
                      >
                        <i className={`fas fa-utensils text-lg
                          ${selectedFoods.has(item.name) 
                            ? 'text-white' 
                            : 'text-emerald-500'}`}
                        ></i>
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-800 mb-1">{item.name || '알 수 없음'}</h3>
                        <div className="text-sm text-gray-500">
                          <div className="flex items-center gap-2">
                            <span>탄수화물 {formatNumber(item.nutrients?.carbohydrates)}g</span>
                            <span>•</span>
                            <span>단백질 {formatNumber(item.nutrients?.protein)}g</span>
                          </div>
                          <div className="mt-1">
                            <span>지방 {formatNumber(item.nutrients?.fat)}g</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-emerald-500 font-medium">
                        {Math.round(item.calories || 0).toLocaleString()} kcal
                      </div>
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all
                        ${selectedFoods.has(item.name)
                          ? 'border-emerald-500 bg-emerald-500'
                          : 'border-gray-300'}`}
                      >
                        {selectedFoods.has(item.name) && (
                          <i className="fas fa-check text-white text-sm"></i>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white rounded-2xl p-8 text-center">
                  <i className="fas fa-search text-5xl text-gray-300 mb-4"></i>
                  <p className="text-gray-600 font-medium text-lg">인식된 음식이 없습니다.</p>
                  <p className="text-sm text-gray-500 mt-2">다시 시도해 주세요.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
      <BottomNav />
    </div>
  );
};

export default OcrResultPage; 