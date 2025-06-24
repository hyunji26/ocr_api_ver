import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

const API_BASE_URL = `http://${window.location.hostname}:8000`;  // 현재 호스트 주소 사용

const ProfilePage = () => {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const fileInputRef = useRef(null);

  const [userStats, setUserStats] = useState({
    weeklyAvgBalance: 0,
    monthlyAvgCalories: 0,
    perfectBalanceDays: 0,
    daysSinceJoined: 0
  });

  const [settings, setSettings] = useState({
    dailyCalorieGoal: 0
  });

  const [userProfile, setUserProfile] = useState({
    name: '',  // 초기값을 빈 문자열로 설정
    email: '',
    profileImage: null
  });

  const [weeklyBalanceScore, setWeeklyBalanceScore] = useState(0);
  const [monthlyStats, setMonthlyStats] = useState({
    averageCalories: 0
  });

  const [tempCalorieGoal, setTempCalorieGoal] = useState(0);

  // 페이지 마운트 시 스크롤을 맨 위로 이동
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const userResponse = await fetch(`${API_BASE_URL}/api/v1/balance/users/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUserProfile(prev => ({
            ...prev,
            name: userData.name,  // 회원가입 시 입력한 이름을 그대로 사용
            email: userData.email
          }));
        }
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
      }
    };

    const fetchUserSettings = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // 사용자 설정 가져오기
        const statsResponse = await fetch(`${API_BASE_URL}/api/v1/balance/stats`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (statsResponse.ok) {
          const data = await statsResponse.json();
          setSettings(prev => ({
            ...prev,
            dailyCalorieGoal: data.daily_calorie_goal
          }));
          setTempCalorieGoal(data.daily_calorie_goal);
        }
      } catch (error) {
        console.error('Failed to fetch user settings:', error);
      }
    };

    const fetchUserStats = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const userId = localStorage.getItem('userId');
        if (!userId) {
          navigate('/login');
          return;
        }

        // 가입 일수 조회
        const daysResponse = await fetch(
          `${API_BASE_URL}/api/v1/balance/user/days-since-joined`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (daysResponse.ok) {
          const daysData = await daysResponse.json();
          setUserStats(prev => ({
            ...prev,
            daysSinceJoined: daysData.days
          }));
        }

        // 기존 월간 통계 데이터 가져오기
        const currentDate = new Date();
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;

        const monthlyResponse = await fetch(
          `${API_BASE_URL}/api/v1/balance/monthly/${userId}/${year}/${month}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (!monthlyResponse.ok) {
          if (monthlyResponse.status === 401) {
            navigate('/login');
            return;
          }
          throw new Error(`월간 통계 조회 실패: ${monthlyResponse.status}`);
        }

        if (monthlyResponse.ok) {
          const monthlyData = await monthlyResponse.json();
          
          // 월간 평균 칼로리 계산
          let totalCalories = 0;
          let daysWithMeals = 0;
          
          Object.values(monthlyData.daily_meals).forEach(dayData => {
            if (dayData && dayData.total_calories > 0) {
              totalCalories += dayData.total_calories;
              daysWithMeals++;
            }
          });

          const averageCalories = daysWithMeals > 0 
            ? Math.round(totalCalories / daysWithMeals) 
            : 0;

          setMonthlyStats({ averageCalories });
          setUserStats(prev => ({
            ...prev,
            monthlyAvgCalories: averageCalories,
            perfectBalanceDays: monthlyData.perfect_balance_count || 0
          }));
        }
      } catch (error) {
        console.error('Failed to fetch user stats:', error);
      }
    };

    const fetchWeeklyScore = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/balance/weekly-score`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setWeeklyBalanceScore(data.weekly_balance_score);
        }
      } catch (error) {
        console.error('주간 밸런스 점수 조회 중 오류 발생:', error);
      }
    };

    fetchUserProfile();
    fetchUserSettings();
    fetchUserStats();
    fetchWeeklyScore();
  }, [navigate]);

  const handleCalorieInputChange = (e) => {
    setTempCalorieGoal(e.target.value);
  };

  const handleCalorieGoalSave = async () => {
    const newGoal = parseInt(tempCalorieGoal);
    if (isNaN(newGoal)) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/balance/user/calorie-goal?daily_calorie_goal=${newGoal}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({
          ...prev,
          dailyCalorieGoal: data.daily_calorie_goal
        }));
        alert('목표 칼로리가 저장되었습니다.');
      } else {
        alert('저장에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      console.error('Error updating calorie goal:', error);
      alert('저장 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    navigate('/login');
  };

  const handleCalorieGoalChange = async (e) => {
    const newGoal = parseInt(e.target.value);
    if (isNaN(newGoal)) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/balance/user/calorie-goal?daily_calorie_goal=${newGoal}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSettings(prev => ({
          ...prev,
          dailyCalorieGoal: newGoal
        }));
      } else {
        console.error('Failed to update calorie goal');
      }
    } catch (error) {
      console.error('Error updating calorie goal:', error);
    }
  };

  const handleSaveProfile = async () => {
    try {
      setShowToast(true);
      setIsModalOpen(false);
      setTimeout(() => {
        setShowToast(false);
      }, 3000);
    } catch (error) {
      console.error('프로필 저장 중 오류 발생:', error);
    }
  };

  return (
    <div className="min-h-screen bg-emerald-400 text-gray-800 flex flex-col">
      {/* Header */}
      <header className="p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">프로필</h1>
        <button 
          onClick={handleLogout}
          className="bg-white/30 text-emerald-800 px-4 py-1.5 rounded-full text-sm whitespace-nowrap cursor-pointer"
        >
          로그아웃
        </button>
      </header>

      {/* Profile Card */}
      <div className="mx-4 bg-white/80 rounded-xl p-4 shadow-sm relative">
        <div className="flex items-center">
          <div className="relative">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
              {userProfile.profileImage ? (
                <img
                  src={userProfile.profileImage}
                  alt="프로필"
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <i className="fas fa-user text-emerald-500 text-2xl"></i>
              )}
            </div>
            <div
              className="absolute bottom-0 right-0 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <i className="fas fa-camera text-white text-xs"></i>
            </div>
          </div>
          <div className="ml-4">
            <div className="flex items-center">
              <h2 className="text-lg font-bold">{userProfile.name}</h2>
              <button
                className="ml-2 text-emerald-500 cursor-pointer"
                onClick={() => setIsModalOpen(true)}
              >
                <i className="fas fa-pen text-xs"></i>
              </button>
            </div>
            <p className="text-sm text-gray-500">활동한지 {userStats.daysSinceJoined}일째</p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-emerald-50 p-4 rounded-xl">
            <p className="text-xs text-gray-600">주간 평균 밸런스</p>
            <p className="text-2xl font-bold text-emerald-500 mt-1">{weeklyBalanceScore}점</p>
            <p className="text-[10px] text-gray-500 mt-1">지난 7일 평균</p>
          </div>
          <div className="bg-blue-50 p-4 rounded-xl">
            <p className="text-xs text-gray-600">월간 평균 칼로리</p>
            <p className="text-2xl font-bold text-blue-500 mt-1">{userStats.monthlyAvgCalories}kcal</p>
            <p className="text-[10px] text-gray-500 mt-1">이번 달 기준</p>
          </div>
          <div className="bg-orange-50 p-4 rounded-xl">
            <p className="text-xs text-gray-600">완벽 밸런스 달성</p>
            <p className="text-2xl font-bold text-orange-500 mt-1">{userStats.perfectBalanceDays}일</p>
            <p className="text-[10px] text-gray-500 mt-1">밸런스 90점 이상</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-xl">
            <p className="text-xs text-gray-600">건강식단 연속</p>
            <p className="text-2xl font-bold text-purple-500 mt-1">{userStats.daysSinceJoined}일</p>
            <p className="text-[10px] text-gray-500 mt-1">가입일 기준</p>
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="mx-4 mt-4 bg-white/80 rounded-xl p-4 shadow-sm">
        <h3 className="text-lg font-bold mb-3">설정</h3>

        <div className="mb-4">
          <label className="text-sm text-gray-600 block mb-2">
            하루 목표 칼로리
          </label>
          <div className="flex">
            <input
              type="number"
              className="flex-1 p-3 border border-gray-200 rounded-l-lg focus:outline-none focus:border-emerald-500"
              value={tempCalorieGoal}
              onChange={(e) => setTempCalorieGoal(e.target.value)}
            />
            <button
              className="bg-emerald-500 text-white px-4 rounded-r-lg whitespace-nowrap cursor-pointer"
              onClick={handleCalorieGoalSave}
            >
              저장
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">권장 칼로리: 2000kcal</p>
        </div>
      </div>

      {/* Profile Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-t-2xl w-full max-h-[80vh] overflow-auto animate-slideUp">
            <div className="p-4 border-b border-gray-100">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold">프로필 수정</h3>
                <button
                  className="text-gray-500 cursor-pointer"
                  onClick={() => setIsModalOpen(false)}
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
            </div>

            <div className="p-4">
              {/* Profile Image */}
              <div className="flex flex-col items-center mb-6">
                <div className="relative mb-3">
                  <div className="w-24 h-24 bg-emerald-100 rounded-full flex items-center justify-center">
                    {userProfile.profileImage ? (
                      <img
                        src={userProfile.profileImage}
                        alt="프로필"
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <i className="fas fa-user text-emerald-500 text-4xl"></i>
                    )}
                  </div>
                  <div 
                    className="absolute bottom-0 right-0 w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <i className="fas fa-camera text-white"></i>
                  </div>
                </div>
                <p className="text-sm text-gray-500">프로필 이미지 변경</p>
              </div>

              {/* Name */}
              <div className="mb-4">
                <label className="text-sm text-gray-600 block mb-2">이름</label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-500"
                  value={userProfile.name}
                  onChange={(e) => setUserProfile({...userProfile, name: e.target.value})}
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-4 border-t border-gray-100 flex space-x-3">
              <button
                className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg whitespace-nowrap cursor-pointer"
                onClick={() => setIsModalOpen(false)}
              >
                취소
              </button>
              <button
                className="flex-1 py-3 bg-emerald-500 text-white rounded-lg whitespace-nowrap cursor-pointer"
                onClick={handleSaveProfile}
              >
                저장하기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Message */}
      {showToast && (
        <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg animate-fadeIn">
          변경사항이 저장되었습니다
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-in-out;
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-in-out;
        }
      `}</style>

      <BottomNav />
    </div>
  );
};

export default ProfilePage; 