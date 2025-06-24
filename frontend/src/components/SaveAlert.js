import React from 'react';

const SaveAlert = ({ onClose }) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 flex justify-center items-end z-50 p-4 animate-slide-up">
      <div className="bg-gray-900 text-white px-5 py-4 rounded-2xl shadow-lg flex items-center gap-3 max-w-sm w-full">
        <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
          <i className="fas fa-check text-sm"></i>
        </div>
        <p className="text-base">저장되었습니다</p>
      </div>
    </div>
  );
};

export default SaveAlert; 