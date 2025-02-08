// src/App.js
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import AboutPage from './AboutPage';
import AuthPage from './AuthPage';
import DevicePage from './DevicePage'; // 导入 DevicePage

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/devices" element={<DevicePage />} /> {/* 添加路由 */}
    </Routes>
  );
}

export default App;
