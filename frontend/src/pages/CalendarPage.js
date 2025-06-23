import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

const API_BASE_URL = `http://${window.location.hostname}:8000`;  // 현재 호스트 주소 사용

const CalendarPage = () => {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [monthlyData, setMonthlyData] = useState({});
  const [selectedDateMeals, setSelectedDateMeals] = useState(null);
  const [viewMode, setViewMode] = useState('calendar'); // 'calendar', 'stats', 'challenges'
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [streakData, setStreakData] = useState({
    currentStreak: 0,
    longestStreak: 0,
    totalPerfectDays: 0
  });
  const [monthlyStats, setMonthlyStats] = useState({
    averageBalance: 0,
    averageCalories: 0,
    waterGoalAchievement: 0,
    breakfastCount: 0,
    mostFrequentMenu: '',
    preferredMealTime: '12:00'
  });

  const userId = localStorage.getItem('userId');

  const challenges = [
    {
      id: 1,
      title: "단백질 챔피언",
      description: "7일 연속 단백질 섭취 목표 달성",
      duration: 7,
      target: "일일 단백질 80g 이상",
      reward: "뱃지 획득",
      progress: 5,
      type: "protein"
    },
    {
      id: 2,
      title: "물 마시기 챌린지",
      description: "30일 동안 매일 2L 이상의 물 섭취",
      duration: 30,
      target: "일일 2L",
      reward: "프리미엄 기능 해금",
      progress: 25,
      type: "water"
    },
    {
      id: 3,
      title: "완벽한 밸런스",
      description: "5일 연속 영양 밸런스 90점 이상 달성",
      duration: 5,
      target: "밸런스 90점+",
      reward: "특별 뱃지",
      progress: 3,
      type: "balance"
    }
  ];

  useEffect(() => {
    if (!userId) {
      navigate('/login');
      return;
    }

    const fetchMonthlyData = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/balance/monthly/${userId}/${currentDate.getFullYear()}/${currentDate.getMonth() + 1}`
        );
        if (!response.ok) throw new Error('Failed to fetch monthly data');
        const data = await response.json();
        setMonthlyData(data);
      } catch (error) {
        console.error('Error fetching monthly data:', error);
      }
    };

    const fetchUserStats = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/balance/stats/${userId}`
        );
        if (!response.ok) throw new Error('Failed to fetch user stats');
        const data = await response.json();
        setMonthlyStats(data);
      } catch (error) {
        console.error('Error fetching user stats:', error);
      }
    };

    const fetchUserStreak = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/balance/streak/${userId}`
        );
        if (!response.ok) throw new Error('Failed to fetch user streak');
        const data = await response.json();
        setStreakData(data);
      } catch (error) {
        console.error('Error fetching user streak:', error);
      }
    };

    fetchMonthlyData();
    fetchUserStats();
    fetchUserStreak();
  }, [userId, currentDate, navigate]);

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    const days = [];
    const firstDayOfWeek = firstDay.getDay();
    
    // 이전 달의 마지막 날짜들
    for (let i = 0; i < firstDayOfWeek; i++) {
      const prevDate = new Date(year, month, -i);
      days.unshift({
        date: prevDate,
        isCurrentMonth: false
      });
    }
    
    // 현재 달의 날짜들
    for (let i = 1; i <= lastDay.getDate(); i++) {
      const currentDate = new Date(year, month, i);
      days.push({
        date: currentDate,
        isCurrentMonth: true
      });
    }
    
    // 다음 달의 시작 날짜들
    const remainingDays = 42 - days.length; // 6주 달력을 위해
    for (let i = 1; i <= remainingDays; i++) {
      const nextDate = new Date(year, month + 1, i);
      days.push({
        date: nextDate,
        isCurrentMonth: false
      });
    }
    
    return days;
  };

  const formatDate = (date) => {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };

  const handleDateClick = (date) => {
    const formattedDate = formatDate(date);
    setSelectedDate(date);
    setSelectedDateMeals(monthlyData[formattedDate]);
  };

  const handleMonthChange = (offset) => {
    const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + offset, 1);
    setCurrentDate(newDate);
    setSelectedDate(null);
    setSelectedDateMeals(null);
  };

  const renderMoodEmoji = (mood) => {
    const moodEmojis = {
      '행복': '😊',
      '보통': '😐',
      '피곤': '😫',
      '스트레스': '😤',
      '활력': '💪'
    };
    return moodEmojis[mood] || '😊';
  };

  const renderWeatherIcon = (weather) => {
    const weatherIcons = {
      '맑음': '☀️',
      '흐림': '☁️',
      '비': '🌧️',
      '눈': '❄️'
    };
    return weatherIcons[weather] || '☀️';
  };

  const calculateNutrientProgress = (nutrient, value) => {
    const targets = {
      protein: 100,
      carbs: 300,
      fat: 65,
      fiber: 25
    };
    return (value / targets[nutrient]) * 100;
  };

  const days = getDaysInMonth(currentDate);
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  const renderCalendarView = () => (
    <>
      {/* 달력 그리드 */}
      <div className="grid grid-cols-7 gap-1">
        {days.map((dayInfo, index) => {
          const formattedDate = formatDate(dayInfo.date);
          const dayData = monthlyData[formattedDate];
          const isSelected = selectedDate && formatDate(selectedDate) === formattedDate;
          
          return (
            <div
              key={index}
              onClick={() => handleDateClick(dayInfo.date)}
              className={`aspect-square p-1 rounded-lg transition-all ${
                dayInfo.isCurrentMonth 
                  ? 'bg-white bg-opacity-20 hover:bg-opacity-30' 
                  : 'bg-transparent'
              } ${
                isSelected ? 'ring-2 ring-emerald-500' : ''
              }`}
            >
              <div className={`text-sm font-medium ${
                !dayInfo.isCurrentMonth ? 'text-gray-400' :
                dayInfo.date.getDay() === 0 ? 'text-red-500' :
                dayInfo.date.getDay() === 6 ? 'text-blue-500' :
                'text-gray-700'
              }`}>
                {dayInfo.date.getDate()}
              </div>
              {dayData && (
                <div className="mt-1">
                  <div className="h-1 bg-emerald-500 rounded-full" 
                    style={{ width: `${(dayData.balanceScore/100) * 100}%` }}
                  />
                  <div className="text-xs text-gray-600 mt-1">
                    {dayData.totalCalories}kcal
                  </div>
                  {dayData.mood && (
                    <div className="text-xs">{renderMoodEmoji(dayData.mood)}</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 선택된 날짜 상세 정보 */}
      {selectedDateMeals && (
        <div className="mt-6 space-y-4">
          {/* 날씨, 기분, 운동 요약 */}
          <div className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <div className="text-2xl">{renderWeatherIcon(selectedDateMeals.weather)}</div>
                <div className="text-2xl">{renderMoodEmoji(selectedDateMeals.mood)}</div>
              </div>
              <div className="text-sm text-gray-600">
                {selectedDateMeals.exercise && (
                  <div className="flex items-center">
                    <i className="fas fa-running mr-2"></i>
                    {selectedDateMeals.exercise}
                  </div>
                )}
              </div>
            </div>
            {selectedDateMeals.waterIntake && (
              <div className="mt-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">물 섭취량</span>
                  <span className="text-sm font-medium">{selectedDateMeals.waterIntake}ml</span>
                </div>
                <div className="mt-1 h-2 bg-blue-100 rounded-full">
                  <div 
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${Math.min((selectedDateMeals.waterIntake / 2000) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* 영양소 요약 */}
          <div className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-4">
            <h3 className="text-lg font-bold text-gray-800 mb-3">영양소 섭취 현황</h3>
            <div className="space-y-3">
              {Object.entries(selectedDateMeals.meals[0].nutrients).map(([nutrient, value]) => (
                <div key={nutrient}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm capitalize">{nutrient}</span>
                    <span className="text-sm font-medium">{value}g</span>
                  </div>
                  <div className="h-2 bg-emerald-100 rounded-full">
                    <div 
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${calculateNutrientProgress(nutrient, value)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 식사 상세 */}
          <div className="space-y-4">
            {selectedDateMeals.meals.map((meal, index) => (
              <div key={index} className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-4">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <div className="text-sm text-gray-600">{meal.type}</div>
                    <div className="font-medium text-gray-800">{meal.menu}</div>
                  </div>
                  <div className="text-emerald-600 font-medium">
                    {meal.calories}kcal
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {meal.tags.map((tag, tagIndex) => (
                    <span 
                      key={tagIndex}
                      className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );

  const renderStatsView = () => (
    <div className="space-y-6">
      {/* 연속 기록 */}
      <div className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">나의 기록</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-500">{streakData.currentStreak}</div>
            <div className="text-sm text-gray-600">현재 연속</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-500">{streakData.longestStreak}</div>
            <div className="text-sm text-gray-600">최장 연속</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-500">{streakData.totalPerfectDays}</div>
            <div className="text-sm text-gray-600">완벽한 날</div>
          </div>
        </div>
      </div>

      {/* 월간 통계 */}
      <div className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">이번 달 통계</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-600">평균 밸런스 점수</span>
              <span className="text-sm font-medium">85점</span>
            </div>
            <div className="h-2 bg-emerald-100 rounded-full">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: '85%' }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-600">평균 칼로리</span>
              <span className="text-sm font-medium">2,100kcal</span>
            </div>
            <div className="h-2 bg-emerald-100 rounded-full">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: '70%' }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-600">물 섭취 목표 달성</span>
              <span className="text-sm font-medium">80%</span>
            </div>
            <div className="h-2 bg-emerald-100 rounded-full">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: '80%' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* 식사 패턴 */}
      <div className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">식사 패턴</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">아침 식사 횟수</span>
            <span className="text-sm font-medium">25/30일</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">가장 자주 먹은 음식</span>
            <span className="text-sm font-medium">닭가슴살 샐러드</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">선호하는 식사 시간</span>
            <span className="text-sm font-medium">12:30 PM</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderChallengesView = () => (
    <div className="space-y-4">
      {challenges.map((challenge) => (
        <div 
          key={challenge.id}
          className="bg-white bg-opacity-20 backdrop-blur-lg rounded-xl p-6"
          onClick={() => setSelectedChallenge(challenge)}
        >
          <div className="flex justify-between items-start mb-3">
            <div>
              <h3 className="text-lg font-bold text-gray-800">{challenge.title}</h3>
              <p className="text-sm text-gray-600">{challenge.description}</p>
            </div>
            <div className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-sm">
              {challenge.progress}/{challenge.duration}일
            </div>
          </div>
          <div className="h-2 bg-emerald-100 rounded-full">
            <div 
              className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${(challenge.progress / challenge.duration) * 100}%` }}
            ></div>
          </div>
          <div className="mt-3 flex justify-between items-center text-sm">
            <span className="text-gray-600">목표: {challenge.target}</span>
            <span className="text-emerald-600">보상: {challenge.reward}</span>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 font-sans">
      <div className="max-w-lg mx-auto bg-transparent px-6 pb-24">
        {/* 상단 헤더 */}
        <div className="pt-6 sticky top-0 bg-gradient-to-b from-emerald-400 to-transparent pb-4 z-10">
          <div className="flex justify-between items-center mb-6">
            {viewMode === 'calendar' && (
              <>
                <button 
                  onClick={() => handleMonthChange(-1)}
                  className="p-2 rounded-lg bg-white bg-opacity-20 text-gray-700 hover:bg-opacity-30"
                >
                  <i className="fas fa-chevron-left"></i>
                </button>
                <h1 className="text-xl font-bold text-gray-800">
                  {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
                </h1>
                <button 
                  onClick={() => handleMonthChange(1)}
                  className="p-2 rounded-lg bg-white bg-opacity-20 text-gray-700 hover:bg-opacity-30"
                >
                  <i className="fas fa-chevron-right"></i>
                </button>
              </>
            )}
            {viewMode === 'stats' && (
              <h1 className="text-xl font-bold text-gray-800 w-full text-center">통계</h1>
            )}
            {viewMode === 'challenges' && (
              <h1 className="text-xl font-bold text-gray-800 w-full text-center">챌린지</h1>
            )}
          </div>

          {/* 뷰 모드 선택 */}
          <div className="flex justify-center space-x-2 mb-4">
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-4 py-2 rounded-lg transition-all ${
                viewMode === 'calendar'
                  ? 'bg-white text-emerald-600'
                  : 'bg-white bg-opacity-20 text-gray-600'
              }`}
            >
              캘린더
            </button>
            <button
              onClick={() => setViewMode('stats')}
              className={`px-4 py-2 rounded-lg transition-all ${
                viewMode === 'stats'
                  ? 'bg-white text-emerald-600'
                  : 'bg-white bg-opacity-20 text-gray-600'
              }`}
            >
              통계
            </button>
            <button
              onClick={() => setViewMode('challenges')}
              className={`px-4 py-2 rounded-lg transition-all ${
                viewMode === 'challenges'
                  ? 'bg-white text-emerald-600'
                  : 'bg-white bg-opacity-20 text-gray-600'
              }`}
            >
              챌린지
            </button>
          </div>

          {viewMode === 'calendar' && (
            <div className="grid grid-cols-7 mb-2">
              {weekDays.map((day, index) => (
                <div 
                  key={day} 
                  className={`text-center text-sm font-medium ${
                    index === 0 ? 'text-red-500' : 
                    index === 6 ? 'text-blue-500' : 
                    'text-gray-600'
                  }`}
                >
                  {day}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 메인 컨텐츠 */}
        {viewMode === 'calendar' && renderCalendarView()}
        {viewMode === 'stats' && renderStatsView()}
        {viewMode === 'challenges' && renderChallengesView()}

        {/* 하단 네비게이션 */}
        <BottomNav />
      </div>
    </div>
  );
};

export default CalendarPage; 