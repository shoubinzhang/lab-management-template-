// src/AuthPage.js
import React, { useState } from 'react';

function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [message, setMessage] = useState('');

  const toggleForm = () => {
    setIsLogin(!isLogin);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const url = isLogin ? 'http://localhost:5000/login' : 'http://localhost:5000/register';
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    });

    const data = await response.json();
    if (response.ok) {
      setMessage(data.message);
    } else {
      setMessage(data.message);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  return (
    <div className="auth-page">
      <h2>{isLogin ? '登录' : '注册'}</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>用户名：</label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>密码：</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit">{isLogin ? '登录' : '注册'}</button>
      </form>
      {message && <p>{message}</p>}
      <button onClick={toggleForm}>
        {isLogin ? '没有账号？注册' : '已有账号？登录'}
      </button>
    </div>
  );
}

export default AuthPage;
