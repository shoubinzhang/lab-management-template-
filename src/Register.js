import React, { useState } from 'react';
import axios from 'axios'; // 用于发送请求

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage('');

    try {
      // 发送注册请求
      const response = await axios.post('https://api.example.com/register', {
        username,
        password,
      });

      if (response.data.success) {
        // 注册成功后处理
        console.log('注册成功', response.data);
        // 可以重定向或做其他处理
      } else {
        // 显示错误信息
        setErrorMessage('注册失败，请重试！');
      }
    } catch (error) {
      // 捕获并处理错误
      console.error('注册请求失败', error);
      setErrorMessage('注册请求失败，请检查网络或稍后再试！');
    }

    setIsLoading(false);
  };

  return (
    <div className="container">
      <div className="form-container">
        <h2>Register</h2>
        {errorMessage && <div className="error-message">{errorMessage}</div>}
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="请输入用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="请输入密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? '正在注册...' : '注册'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Register;
