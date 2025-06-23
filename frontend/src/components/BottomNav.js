import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const BottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white bg-opacity-90 backdrop-blur-lg shadow-lg px-6 py-2">
      <div className="max-w-lg mx-auto flex justify-between items-center">
        <button
          onClick={() => navigate('/')}
          className={`flex flex-col items-center p-2 ${
            isActive('/') ? 'text-emerald-500' : 'text-gray-500'
          }`}
        >
          <i className="fas fa-home text-xl"></i>
          <span className="text-xs mt-1">홈</span>
        </button>

        <button
          onClick={() => navigate('/meal-log')}
          className={`flex flex-col items-center p-2 ${
            isActive('/meal-log') ? 'text-emerald-500' : 'text-gray-500'
          }`}
        >
          <i className="fas fa-utensils text-xl"></i>
          <span className="text-xs mt-1">식사기록</span>
        </button>

        <button
          onClick={() => navigate('/calendar')}
          className={`flex flex-col items-center p-2 ${
            isActive('/calendar') ? 'text-emerald-500' : 'text-gray-500'
          }`}
        >
          <i className="fas fa-calendar text-xl"></i>
          <span className="text-xs mt-1">캘린더</span>
        </button>

        <button
          onClick={() => navigate('/profile')}
          className={`flex flex-col items-center p-2 ${
            isActive('/profile') ? 'text-emerald-500' : 'text-gray-500'
          }`}
        >
          <i className="fas fa-user text-xl"></i>
          <span className="text-xs mt-1">프로필</span>
        </button>
      </div>
    </nav>
  );
};

export default BottomNav;
