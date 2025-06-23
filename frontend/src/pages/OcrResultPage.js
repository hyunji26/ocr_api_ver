import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

// API 기본 URL 설정
const API_BASE_URL = 'http://192.168.45.153:8000';  // 백엔드 서버 IP로 직접 설정

console.log('Current hostname:', window.location.hostname);
console.log('API Base URL:', API_BASE_URL);

const OcrResultPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(1);
  const [selectedFoods, setSelectedFoods] = useState(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [existingStats, setExistingStats] = useState({
    total_calories: 0,
    nutrients: {
      carbohydrates: 0,
      protein: 0,
      fat: 0
    },
    meal_calories: []
  });
  
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

  const processResults = () => {
    const data = location.state?.results;
    if (!data) return [];
    return data.found_foods || [];
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
      const nutrition = item.nutrition_info || {};
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
        const mealData = {
          meal_type: mealType.toLowerCase(),
          calories: parseFloat(item.nutrition_info?.calories || 0),
          carbohydrates: parseFloat(item.nutrition_info?.nutrients?.carbohydrates || 0),
          protein: parseFloat(item.nutrition_info?.nutrients?.protein || 0),
          fat: parseFloat(item.nutrition_info?.nutrients?.fat || 0)
        };

        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/balance/meals`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(mealData),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to save meal');
        }

        await fetchBalanceStats(); // ← 새로고침 함수 호출
      }

      // 저장 성공 후 기존 통계 업데이트
      const token = localStorage.getItem('token');
      const statsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      // 식사별 칼로리 정보도 업데이트
      const mealsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/meals`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (statsResponse.ok && mealsResponse.ok) {
        const newStats = await statsResponse.json();
        const mealCalories = await mealsResponse.json();
        
        setExistingStats({
          total_calories: newStats.total_calories || 0,
          nutrients: {
            carbohydrates: newStats.nutrients?.carbohydrates || 0,
            protein: newStats.nutrients?.protein || 0,
            fat: newStats.nutrients?.fat || 0
          },
          meal_calories: mealCalories  // 식사별 칼로리 정보 추가
        });
        // 선택된 음식 초기화
        setSelectedFoods(new Set());
      }

      alert('선택한 음식이 저장되었습니다.');
      navigate('/');
    } catch (error) {
      console.error('Error saving meals:', error);
      alert('음식 저장 중 오류가 발생했습니다: ' + error.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 font-sans relative pb-[72px]">
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
                        <span>탄수화물 {formatNumber(item.nutrition_info?.nutrients?.carbohydrates)}g</span>
                        <span>•</span>
                        <span>단백질 {formatNumber(item.nutrition_info?.nutrients?.protein)}g</span>
                      </div>
                      <div className="mt-1">
                        <span>지방 {formatNumber(item.nutrition_info?.nutrients?.fat)}g</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-emerald-500 font-medium">
                    {Math.round(item.nutrition_info?.calories || 0).toLocaleString()} kcal
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

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
};

export default OcrResultPage; 