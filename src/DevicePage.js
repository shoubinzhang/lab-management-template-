// src/DevicePage.js
import React, { useState, useEffect } from 'react';

function DevicePage() {
  const [devices, setDevices] = useState([]);
  const [newDevice, setNewDevice] = useState('');

  // 获取设备列表
  useEffect(() => {
    fetch('http://localhost:5000/devices')
      .then((res) => res.json())
      .then((data) => setDevices(data));
  }, []);

  // 添加设备
  const handleAddDevice = async () => {
    if (newDevice) {
      const response = await fetch('http://localhost:5000/devices', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newDevice }),
      });

      const data = await response.json();
      if (response.ok) {
        setDevices((prevDevices) => [...prevDevices, { name: newDevice }]);
        setNewDevice('');
      } else {
        alert(data.message);
      }
    }
  };

  // 删除设备
  const handleDeleteDevice = async (deviceName) => {
    const response = await fetch(`http://localhost:5000/devices/${deviceName}`, {
      method: 'DELETE',
    });

    if (response.ok) {
      setDevices(devices.filter((device) => device.name !== deviceName));
    }
  };

  return (
    <div className="device-page">
      <h2>设备管理</h2>
      <input
        type="text"
        value={newDevice}
        onChange={(e) => setNewDevice(e.target.value)}
        placeholder="输入设备名称"
      />
      <button onClick={handleAddDevice}>添加设备</button>

      <ul>
        {devices.map((device, index) => (
          <li key={index}>
            {device.name} <button onClick={() => handleDeleteDevice(device.name)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default DevicePage;
