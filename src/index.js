import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';  // 使用 BrowserRouter 包裹整个应用
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

// 通过 Router 包裹 App 组件
root.render(
  <Router>
    <App />
  </Router>
);

