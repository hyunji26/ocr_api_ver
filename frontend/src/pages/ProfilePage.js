import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

const API_BASE_URL = 'http://192.168.45.153:8000';

const ProfilePage = () => {
  const navigate = useNavigate();
  const [userStats, setUserStats] = useState({
    totalMeals: 0,
    averageBalance: 0,
    streakDays: 0,
    goalAchievements: 0
  });

  const [settings, setSettings] = useState({
    dailyCalorieGoal: 2000,
    notifications: true,
    darkMode: false
  });

  useEffect(() => {
    const fetchUserStats = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // TODO: 실제 API 연동 시 구현
        // 현재는 더미 데이터 사용
        setUserStats({
          totalMeals: 42,
          averageBalance: 85,
          streakDays: 7,
          goalAchievements: 12
        });
      } catch (error) {
        console.error('Failed to fetch user stats:', error);
      }
    };

    fetchUserStats();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    navigate('/login');
  };

  const handleCalorieGoalChange = (e) => {
    setSettings(prev => ({
      ...prev,
      dailyCalorieGoal: e.target.value
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 font-sans">
      <div className="max-w-lg mx-auto bg-transparent px-6 pb-24">
        {/* Header */}
        <header className="pt-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">프로필</h1>
          <button
            onClick={handleLogout}
            className="text-sm px-4 py-2 rounded-lg bg-white bg-opacity-20 text-gray-700 hover:bg-opacity-30 transition-all"
          >
            로그아웃
          </button>
        </header>

        {/* Profile Stats */}
        <div className="mt-8 bg-white bg-opacity-20 rounded-xl p-6">
          <div className="flex items-center mb-6">
            <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center">
              <i className="fas fa-user text-3xl text-emerald-500"></i>
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-bold text-gray-800">건강한 식단러</h2>
              <p className="text-sm text-gray-600">함께한지 {userStats.streakDays}일째</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white bg-opacity-50 rounded-xl p-4">
              <div className="text-sm text-gray-600">식단 기록</div>
              <div className="text-2xl font-bold text-gray-800">{userStats.totalMeals}회</div>
            </div>
            <div className="bg-white bg-opacity-50 rounded-xl p-4">
              <div className="text-sm text-gray-600">평균 밸런스</div>
              <div className="text-2xl font-bold text-emerald-500">{userStats.averageBalance}점</div>
            </div>
            <div className="bg-white bg-opacity-50 rounded-xl p-4">
              <div className="text-sm text-gray-600">연속 기록</div>
              <div className="text-2xl font-bold text-amber-500">{userStats.streakDays}일</div>
            </div>
            <div className="bg-white bg-opacity-50 rounded-xl p-4">
              <div className="text-sm text-gray-600">목표 달성</div>
              <div className="text-2xl font-bold text-blue-500">{userStats.goalAchievements}회</div>
            </div>
          </div>
        </div>

        {/* Settings */}
        <div className="mt-6 bg-white bg-opacity-20 rounded-xl p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">설정</h3>
          
          <div className="space-y-4">
            {/* Calorie Goal Setting */}
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                하루 목표 칼로리
              </label>
              <div className="flex items-center">
                <input
                  type="number"
                  value={settings.dailyCalorieGoal}
                  onChange={handleCalorieGoalChange}
                  className="w-full px-4 py-2 rounded-lg bg-white bg-opacity-50 text-gray-800"
                  step="100"
                  min="1000"
                  max="5000"
                />
                <span className="ml-2 text-gray-600">kcal</span>
              </div>
            </div>

            {/* Notification Setting */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">알림 설정</div>
                <div className="text-xs text-gray-500">식사 시간 알림을 받습니다</div>
              </div>
              <button
                onClick={() => setSettings(prev => ({ ...prev, notifications: !prev.notifications }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  settings.notifications ? 'bg-emerald-500' : 'bg-gray-300'
                } relative`}
              >
                <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-transform ${
                  settings.notifications ? 'translate-x-6' : 'translate-x-0.5'
                }`}></div>
              </button>
            </div>

            {/* Dark Mode Setting */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">다크 모드</div>
                <div className="text-xs text-gray-500">어두운 테마를 사용합니다</div>
              </div>
              <button
                onClick={() => setSettings(prev => ({ ...prev, darkMode: !prev.darkMode }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  settings.darkMode ? 'bg-emerald-500' : 'bg-gray-300'
                } relative`}
              >
                <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-transform ${
                  settings.darkMode ? 'translate-x-6' : 'translate-x-0.5'
                }`}></div>
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Navigation */}
        <BottomNav />
      </div>
    </div>
  );
};

export default ProfilePage; 