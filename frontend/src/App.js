import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import MainPage from './pages/MainPage';
import OcrResultPage from './pages/OcrResultPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/result" element={<OcrResultPage />} />
      </Routes>
    </Router>
  );
}

export default App; 