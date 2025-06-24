import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

const API_BASE_URL = `http://${window.location.hostname}:8000`;  // 현재 호스트 주소 사용

const formatDate = (date) => {
  const days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
  return `${date.getMonth() + 1}월 ${date.getDate()}일 ${days[date.getDay()]}`;
};

const MealLogPage = () => {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [mealLogs, setMealLogs] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedMeal, setSelectedMeal] = useState(null);
  const [totalCalories, setTotalCalories] = useState(0);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const fetchMealData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // 식사 기록 가져오기
        const formattedDate = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`;
        const mealsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/meals?date=${formattedDate}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!mealsResponse.ok) {
          throw new Error(`Failed to fetch data: ${mealsResponse.status}`);
        }

        const mealsData = await mealsResponse.json();
        
        // 식사 데이터 변환 및 총 칼로리 계산
        let total = 0;
        const formattedMeals = Object.entries(mealsData)
          .map(([type, foods]) => {
            const mealCalories = foods.reduce((sum, food) => sum + food.calories, 0);
            total += mealCalories;
            return {
              id: type,
              type: type.charAt(0).toUpperCase() + type.slice(1),
              time: type === 'breakfast' ? '아침' : type === 'lunch' ? '점심' : '저녁',
              foods: foods.map(food => ({
                id: food.id,
                name: food.name,
                calories: food.calories,
                nutrients: {
                  carbs: food.nutrients.carbohydrates,
                  protein: food.nutrients.protein,
                  fat: food.nutrients.fat
                }
              }))
            };
          })
          .filter(meal => meal.foods.length > 0);

        setTotalCalories(total);
        setMealLogs(formattedMeals);
      } catch (error) {
        console.error('Error fetching meal data:', error);
        setMealLogs([]);
      }
    };

    fetchMealData();
  }, [selectedDate, navigate]);

  const handleDateChange = (offset) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(selectedDate.getDate() + offset);
    setSelectedDate(newDate);
    // 스크롤을 즉시 맨 위로 이동
    window.scrollTo(0, 0);
  };

  const handleAddMeal = () => {
    setShowAddModal(true);
  };

  const MealCard = ({ food, mealType, mealTime, mealId }) => (
    <div 
      className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-4 mb-4 cursor-pointer hover:bg-opacity-30 transition-all"
      onClick={() => navigate(`/edit-meal/${mealId}`)}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="flex items-center">
            <span className="text-lg font-bold text-gray-800">{mealType}</span>
            <span className="ml-2 text-sm text-gray-600">{mealTime}</span>
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mt-1">{food.name}</h3>
        </div>
        <div className="text-right">
          <div className="text-sm font-medium text-gray-600">{food.calories} kcal</div>
        </div>
      </div>

      <div className="flex justify-between items-center mt-4">
        <div className="flex space-x-4">
          <div className="text-center">
            <div className="text-xs text-gray-500">탄수화물</div>
            <div className="text-sm font-medium text-gray-700">{food.nutrients.carbs}g</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">단백질</div>
            <div className="text-sm font-medium text-gray-700">{food.nutrients.protein}g</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">지방</div>
            <div className="text-sm font-medium text-gray-700">{food.nutrients.fat}g</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 font-sans">
      <div className="max-w-lg mx-auto bg-transparent px-6 pb-24">
        {/* 상단 날짜 네비게이션 */}
        <div className="pt-6 sticky top-0 bg-gradient-to-b from-emerald-400 to-transparent pb-4 z-10">
          <div className="flex justify-between items-center mb-2">
            <button 
              onClick={() => handleDateChange(-1)}
              className="p-2 rounded-lg bg-white bg-opacity-20 text-gray-700 hover:bg-opacity-30"
            >
              <i className="fas fa-chevron-left"></i>
            </button>
            <h1 className="text-xl font-bold text-gray-800">
              {formatDate(selectedDate)}
            </h1>
            <button 
              onClick={() => handleDateChange(1)}
              className="p-2 rounded-lg bg-white bg-opacity-20 text-gray-700 hover:bg-opacity-30"
            >
              <i className="fas fa-chevron-right"></i>
            </button>
          </div>

          {/* 일일 요약 */}
          <div className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-sm text-gray-600">오늘의 총 칼로리</div>
                <div className="text-2xl font-bold text-gray-800">
                  {totalCalories} kcal
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 식사 목록 */}
        <div className="space-y-4 mt-4">
          {mealLogs.map(meal => (
            meal.foods.map((food, index) => (
              <MealCard 
                key={`${meal.id}-${index}`}
                food={food}
                mealType={meal.type}
                mealTime={meal.time}
                mealId={food.id}
              />
            ))
          ))}
          {mealLogs.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              기록된 식사가 없습니다
            </div>
          )}
        </div>

        {/* Floating Action Button */}
        <div className="fixed bottom-24 right-4">
          <button
            onClick={() => navigate('/manual-meal')}
            className="bg-emerald-500 text-white w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-2xl hover:bg-emerald-600 transition-colors"
          >
            <i className="fas fa-plus"></i>
          </button>
        </div>

        {/* 하단 네비게이션 */}
        <BottomNav />
      </div>

      {/* 식사 추가 모달 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-11/12 max-w-lg">
            <h2 className="text-xl font-bold text-gray-800 mb-4">새로운 식사 기록</h2>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                취소
              </button>
              <button
                onClick={() => {
                  setShowAddModal(false);
                }}
                className="ml-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600"
              >
                추가하기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 식사 상세 모달 */}
      {selectedMeal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-11/12 max-w-lg">
            <h2 className="text-xl font-bold text-gray-800 mb-4">{selectedMeal.type} 상세 정보</h2>
            <button
              onClick={() => setSelectedMeal(null)}
              className="mt-4 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 w-full"
            >
              닫기
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MealLogPage; 