import React, { useEffect, useState } from 'react';

const Records = () => {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/records') // 记录API
      .then((response) => response.json())
      .then((data) => setRecords(data))
      .catch((error) => console.error('Error fetching records:', error));
  }, []);

  return (
    <div>
      <h2>Records</h2>
      <ul>
        {records.map((record) => (
          <li key={record.id}>
            {record.device} - {record.result}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Records;
