import React from 'react';

const MainAlert = ({ message, type = 'success' }) => {
  const getIcon = () => {
    switch (type) {
      case 'error':
        return <i className="fas fa-exclamation text-sm"></i>;
      case 'success':
      default:
        return <i className="fas fa-check text-sm"></i>;
    }
  };

  const getBgColor = () => {
    switch (type) {
      case 'error':
        return 'bg-red-500';
      case 'success':
      default:
        return 'bg-emerald-500';
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 flex justify-center items-end z-50 p-4 animate-slide-up">
      <div className="bg-gray-900 text-white px-5 py-4 rounded-2xl shadow-lg flex items-center gap-3 max-w-sm w-full">
        <div className={`w-6 h-6 rounded-full ${getBgColor()} flex items-center justify-center flex-shrink-0`}>
          {getIcon()}
        </div>
        <p className="text-base">{message}</p>
      </div>
    </div>
  );
};

export default MainAlert; 