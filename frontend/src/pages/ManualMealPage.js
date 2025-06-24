import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = `http://${window.location.hostname}:8000`;

// meal type mapping
const MEAL_TYPE_MAP = {
  '아침': 'breakfast',
  '점심': 'lunch',
  '저녁': 'dinner',
  '간식': 'dinner'  // 간식은 dinner로 처리
};

const ManualMealPage = () => {
  const navigate = useNavigate();
  const [foodItems, setFoodItems] = useState([
    { id: 1, name: '', servingSize: '', calories: '', carbs: '', protein: '', fat: '' }
  ]);
  const [mealType, setMealType] = useState('아침');
  const [mealTime, setMealTime] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 페이지 마운트 시 스크롤을 맨 위로 이동
  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // 현재 시간을 기본값으로 설정
  React.useEffect(() => {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    setMealTime(`${hours}:${minutes}`);
  }, []);

  const handleAddFood = () => {
    const newId = foodItems[foodItems.length - 1].id + 1;
    setFoodItems([...foodItems, { id: newId, name: '', servingSize: '', calories: '', carbs: '', protein: '', fat: '' }]);
  };

  const handleRemoveFood = (id) => {
    if (foodItems.length === 1) return;
    setFoodItems(foodItems.filter(item => item.id !== id));
  };

  const handleInputChange = (id, field, value) => {
    setFoodItems(foodItems.map(item => 
      item.id === id ? { ...item, [field]: value } : item
    ));
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      // 각 음식에 대해 별도의 meal 생성
      for (const item of foodItems) {
        if (!item.name || !item.calories) continue;

        // 현재 날짜와 선택된 시간을 조합하여 ISO 형식의 timestamp 생성
        const [hours, minutes] = mealTime.split(':');
        const timestamp = new Date();
        timestamp.setHours(parseInt(hours), parseInt(minutes), 0, 0);

        const mealData = {
          meal_type: MEAL_TYPE_MAP[mealType],
          timestamp: timestamp.toISOString(),
          food_name: item.name,
          serving_size: item.servingSize || "1회 제공량",
          calories: parseFloat(item.calories) || 0,
          carbohydrates: parseFloat(item.carbs) || 0,
          protein: parseFloat(item.protein) || 0,
          fat: parseFloat(item.fat) || 0
        };

        const response = await fetch(`${API_BASE_URL}/api/v1/balance/meals`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(mealData)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || '식사 기록 저장에 실패했습니다.');
        }
      }

      navigate('/meal-log');
    } catch (error) {
      console.error('Error saving meal:', error);
      alert(error.message || '식사 기록 저장 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-md mx-auto px-4 h-14 flex items-center justify-between">
          <button 
            onClick={() => navigate(-1)}
            className="text-gray-600"
          >
            <i className="fas fa-arrow-left text-lg"></i>
          </button>
          <h1 className="text-lg font-semibold">식사 직접 입력</h1>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="text-emerald-500 font-medium disabled:opacity-50"
          >
            저장
          </button>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6">
        {/* Meal Type & Time */}
        <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm text-gray-600 mb-1">식사 종류</label>
              <select
                value={mealType}
                onChange={(e) => setMealType(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500 bg-white"
              >
                <option value="아침">아침</option>
                <option value="점심">점심</option>
                <option value="저녁">저녁</option>
                <option value="간식">간식</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm text-gray-600 mb-1">식사 시간</label>
              <input
                type="time"
                value={mealTime}
                onChange={(e) => setMealTime(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Food Items */}
        {foodItems.map((item, index) => (
          <div key={item.id} className="bg-white rounded-xl p-4 shadow-sm mb-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-medium">음식 {index + 1}</h3>
              {foodItems.length > 1 && (
                <button
                  onClick={() => handleRemoveFood(item.id)}
                  className="text-red-500"
                >
                  <i className="fas fa-trash-alt"></i>
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">음식 이름</label>
                <input
                  type="text"
                  value={item.name}
                  onChange={(e) => handleInputChange(item.id, 'name', e.target.value)}
                  placeholder="예) 현미밥"
                  className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-1">1회 제공량</label>
                <input
                  type="text"
                  value={item.servingSize}
                  onChange={(e) => handleInputChange(item.id, 'servingSize', e.target.value)}
                  placeholder="예) 200g"
                  className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">칼로리 (kcal)</label>
                  <input
                    type="number"
                    value={item.calories}
                    onChange={(e) => handleInputChange(item.id, 'calories', e.target.value)}
                    placeholder="0"
                    className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">탄수화물 (g)</label>
                  <input
                    type="number"
                    value={item.carbs}
                    onChange={(e) => handleInputChange(item.id, 'carbs', e.target.value)}
                    placeholder="0"
                    className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">단백질 (g)</label>
                  <input
                    type="number"
                    value={item.protein}
                    onChange={(e) => handleInputChange(item.id, 'protein', e.target.value)}
                    placeholder="0"
                    className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">지방 (g)</label>
                  <input
                    type="number"
                    value={item.fat}
                    onChange={(e) => handleInputChange(item.id, 'fat', e.target.value)}
                    placeholder="0"
                    className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Add Food Button */}
        <button
          onClick={handleAddFood}
          className="w-full py-4 border-2 border-dashed border-emerald-200 rounded-xl text-emerald-500 hover:bg-emerald-50 transition-colors"
        >
          <i className="fas fa-plus mr-2"></i>
          음식 추가하기
        </button>
      </div>
    </div>
  );
};

export default ManualMealPage; 