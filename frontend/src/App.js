import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import './App.css';
import MainPage from './pages/MainPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import MealLogPage from './pages/MealLogPage';
import OcrResultPage from './pages/OcrResultPage';
import ManualMealPage from './pages/ManualMealPage';
import EditMealPage from './pages/EditMealPage';
import { MealProvider } from './context/MealContext';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const navigate = useNavigate();

  useEffect(() => {
    // 토큰이 없으면 로그인 페이지로 리다이렉트
    if (!token) {
      navigate('/login');
    }
  }, [token, navigate]);

  if (!token) {
    return null;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const navigate = useNavigate();

  useEffect(() => {
    // 이미 로그인된 상태면 메인 페이지로 리다이렉트
    if (token) {
      navigate('/');
    }
  }, [token, navigate]);

  if (token) {
    return null;
  }

  return children;
};

// 스크롤 처리를 위한 컴포넌트
function ScrollToTop() {
  const location = useLocation();

  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, [location]);

  return null;
}

function App() {
  return (
    <MealProvider>
      <Router>
        <ScrollToTop />
        <Routes>
          {/* 공개 라우트 */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* 보호된 라우트 */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <MainPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/ocr-result"
            element={
              <PrivateRoute>
                <OcrResultPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <ProfilePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/meal-log"
            element={
              <PrivateRoute>
                <MealLogPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/manual-meal"
            element={
              <PrivateRoute>
                <ManualMealPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/edit-meal/:mealId"
            element={
              <PrivateRoute>
                <EditMealPage />
              </PrivateRoute>
            }
          />

          {/* 404 페이지 */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </MealProvider>
  );
}

export default App; 