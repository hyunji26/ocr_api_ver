import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import MainPage from './pages/MainPage';
import OcrResultPage from './pages/OcrResultPage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import MealLogPage from './pages/MealLogPage';
import CalendarPage from './pages/CalendarPage';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
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
          path="/calendar"
          element={
            <PrivateRoute>
              <CalendarPage />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App; 