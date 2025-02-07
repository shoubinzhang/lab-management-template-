import React, { useState, useEffect } from 'react';
import { Route, Routes } from 'react-router-dom';  // 只需要引入 Routes 和 Route
import Register from './Register';
import DeviceManagement from './DeviceManagement';
import Records from './Records';
import Navbar from './Navbar';
import { ThreeDots } from 'react-loader-spinner';  // 使用适合的加载动画

const App = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 模拟数据加载过程，2秒后隐藏加载动画
    setTimeout(() => {
      setLoading(false);
    }, 2000);
  }, []);

  if (loading) {
    return (
      <div className="loading-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <ThreeDots color="#00BFFF" height={80} width={80} />
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <Navbar /> {/* 导航栏 */}
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/devices" element={<DeviceManagement />} />
        <Route path="/records" element={<Records />} />
        <Route path="/" element={<DeviceManagement />} /> {/* 默认页面为设备管理 */}
      </Routes>
    </div>
  );
};

export default App;
