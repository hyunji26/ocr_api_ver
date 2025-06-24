import React from 'react';

const CustomAlert = ({ message, onClose }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="bg-black bg-opacity-50 absolute inset-0" onClick={onClose}></div>
      <div className="bg-white rounded-lg shadow-lg p-4 max-w-[250px] relative">
        <p className="text-sm text-center text-gray-800">{message}</p>
        <button
          onClick={onClose}
          className="mt-3 w-full bg-emerald-500 text-white text-sm py-1.5 rounded-md hover:bg-emerald-600 transition-colors"
        >
          확인
        </button>
      </div>
    </div>
  );
};

export default CustomAlert; 