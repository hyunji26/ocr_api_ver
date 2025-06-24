import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const API_BASE_URL = `http://${window.location.hostname}:8000`;

const EditMealPage = () => {
  const navigate = useNavigate();
  const { mealId } = useParams();
  const [mealData, setMealData] = useState({
    name: '',
    calories: 0,
    nutrients: {
      carbs: 0,
      protein: 0,
      fat: 0
    },
    meal_type: ''
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMealData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/balance/meals/${mealId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch meal data');
        }

        const data = await response.json();
        setMealData({
          name: data.food_name,
          calories: data.calories,
          nutrients: {
            carbs: data.nutrients.carbohydrates,
            protein: data.nutrients.protein,
            fat: data.nutrients.fat
          },
          meal_type: data.meal_type
        });
        setIsLoading(false);
      } catch (error) {
        setError('식사 정보를 불러오는데 실패했습니다.');
        setIsLoading(false);
      }
    };

    fetchMealData();
  }, [mealId, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/v1/balance/meals/${mealId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          food_name: mealData.name,
          calories: Number(mealData.calories),
          carbohydrates: Number(mealData.nutrients.carbs),
          protein: Number(mealData.nutrients.protein),
          fat: Number(mealData.nutrients.fat),
          meal_type: mealData.meal_type === '아침' ? 'breakfast' : 
                    mealData.meal_type === '점심' ? 'lunch' : 'dinner'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '식사 정보 수정에 실패했습니다.');
      }

      navigate('/meal-log');
    } catch (error) {
      setError(error.message);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith('nutrients.')) {
      const nutrientName = name.split('.')[1];
      setMealData(prev => ({
        ...prev,
        nutrients: {
          ...prev.nutrients,
          [nutrientName]: value
        }
      }));
    } else {
      setMealData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const getMealTypeValue = (koreanType) => {
    switch(koreanType) {
      case '아침': return 'breakfast';
      case '점심': return 'lunch';
      case '저녁': return 'dinner';
      default: return 'breakfast';
    }
  };

  const getMealTypeLabel = (englishType) => {
    switch(englishType) {
      case 'breakfast': return '아침';
      case 'lunch': return '점심';
      case 'dinner': return '저녁';
      default: return '아침';
    }
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">로딩 중...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 p-6">
      <div className="max-w-lg mx-auto bg-white rounded-xl shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">식사 정보 수정</h1>
          <button
            onClick={() => navigate('/meal-log')}
            className="text-gray-600 hover:text-gray-800"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              음식 이름
            </label>
            <input
              type="text"
              name="name"
              value={mealData.name}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              칼로리 (kcal)
            </label>
            <input
              type="number"
              name="calories"
              value={mealData.calories}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
              min="0"
              step="0.1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              탄수화물 (g)
            </label>
            <input
              type="number"
              name="nutrients.carbs"
              value={mealData.nutrients.carbs}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
              min="0"
              step="0.01"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              단백질 (g)
            </label>
            <input
              type="number"
              name="nutrients.protein"
              value={mealData.nutrients.protein}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
              min="0"
              step="0.01"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              지방 (g)
            </label>
            <input
              type="number"
              name="nutrients.fat"
              value={mealData.nutrients.fat}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
              min="0"
              step="0.01"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              식사 시간
            </label>
            <select
              name="meal_type"
              value={getMealTypeValue(mealData.meal_type)}
              onChange={(e) => handleInputChange({
                target: {
                  name: 'meal_type',
                  value: getMealTypeLabel(e.target.value)
                }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            >
              <option value="breakfast">아침</option>
              <option value="lunch">점심</option>
              <option value="dinner">저녁</option>
            </select>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/meal-log')}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-500 text-white rounded-md hover:bg-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              수정하기
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditMealPage; 