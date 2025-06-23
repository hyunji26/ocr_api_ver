import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// API 기본 URL 설정
const API_BASE_URL = `http://${window.location.hostname}:8000`;  // 현재 호스트 주소 사용

console.log('Current hostname:', window.location.hostname);
console.log('API Base URL:', API_BASE_URL);

const LoginPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/balance/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Login response:', data);  // 디버깅용
        
        // 토큰과 사용자 ID를 localStorage에 저장
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userId', data.user_id);
        
        // 메인 페이지로 이동
        navigate('/');
      } else {
        const errorData = await response.json();
        console.error('Login failed:', errorData);
        alert('로그인에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      console.error('Error during login:', error);
      alert('로그인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-400 to-emerald-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
        <h1 className="text-2xl font-bold text-center mb-6">NutriScan</h1>
        <p className="text-gray-600 text-center mb-8">
          건강한 식단 관리를 시작해보세요
        </p>
        <button
          onClick={handleRegister}
          disabled={isLoading}
          className={`w-full bg-emerald-500 text-white py-3 rounded-lg transition-colors ${
            isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-emerald-600'
          }`}
        >
          {isLoading ? '처리 중...' : '시작하기'}
        </button>
      </div>
    </div>
  );
};

export default LoginPage; 