import React, { useEffect, useState } from "react";
import axios from "axios";

const DeviceManagement = () => {
    const [devices, setDevices] = useState([]);

    useEffect(() => {
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        const response = await axios.get("/devices");
        setDevices(response.data);
    };

    return (
        <div>
            <h1>Device Management</h1>
            <ul>
                {devices.map((device) => (
                    <li key={device.id}>
                        {device.name} - {device.status}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default DeviceManagement;