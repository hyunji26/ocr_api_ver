import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const BottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { icon: 'fa-home', label: '홈', path: '/' },
    { icon: 'fa-utensils', label: '식단기록', path: '/meals' },
    { icon: 'fa-chart-line', label: '영양분석', path: '/analysis' },
    { icon: 'fa-calendar-alt', label: '캘린더', path: '/calendar' },
    { icon: 'fa-user', label: '프로필', path: '/profile' }
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 max-w-lg mx-auto bg-white rounded-t-xl py-4 px-6">
      <div className="flex justify-between">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.label}
              className="flex flex-col items-center cursor-pointer"
              onClick={() => navigate(item.path)}
            >
              <i className={`fas ${item.icon} ${isActive ? 'text-emerald-500' : 'text-gray-400'} text-xl`}></i>
              <span className="text-xs mt-1 text-gray-600">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default BottomNav;
