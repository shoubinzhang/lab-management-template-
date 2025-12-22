import React, { useEffect, useState } from 'react';

function ExperimentRecords() {
    const [records, setRecords] = useState([]);

    useEffect(() => {
        fetch(`${process.env.REACT_APP_API_URL}/records`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => setRecords(data.records))
            .catch((error) => console.error("Error fetching records:", error));
    }, []);

    return (
        <div>
            <h1>Experiment Records</h1>
            <ul>
                {records.map((record) => (
                    <li key={record.id}>
                        {record.experiment} - {record.date}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default ExperimentRecords;
