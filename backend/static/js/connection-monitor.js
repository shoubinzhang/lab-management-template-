// 连接监控模块 - 确保系统使用真实数据
class ConnectionMonitor {
    constructor() {
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = 5;
        this.retryInterval = 2000;
        this.monitorInterval = null;
        this.connectionCallbacks = [];
    }

    // 添加连接状态变化回调
    onConnectionChange(callback) {
        this.connectionCallbacks.push(callback);
    }

    // 触发连接状态变化
    triggerConnectionChange(connected) {
        this.isConnected = connected;
        this.connectionCallbacks.forEach(callback => {
            try {
                callback(connected);
            } catch (error) {
                console.error('Connection callback error:', error);
            }
        });
    }

    // 检查API连接状态
    async checkConnection() {
        try {
            const response = await fetch(AppConfig.getApiUrl('health'), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: AppConfig.api.timeout
            });

            if (response.ok) {
                this.retryCount = 0;
                if (!this.isConnected) {
                    this.triggerConnectionChange(true);
                }
                return true;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.retryCount++;
            
            if (this.isConnected) {
                this.triggerConnectionChange(false);
            }

            if (this.retryCount >= this.maxRetries) {
                console.error('Maximum retry attempts reached. Connection failed.');
                throw new Error(`连接失败: ${error.message}`);
            }

            console.warn(`Connection attempt ${this.retryCount} failed, retrying in ${this.retryInterval}ms`);
            return false;
        }
    }

    // 开始监控连接
    startMonitoring() {
        if (this.monitorInterval) {
            this.stopMonitoring();
        }

        // 立即检查一次连接状态
        this.checkConnection().catch(error => {
            console.error('Initial connection check failed:', error);
        });

        // 定期检查连接状态
        this.monitorInterval = setInterval(() => {
            this.checkConnection().catch(error => {
                console.error('Periodic connection check failed:', error);
            });
        }, 10000); // 每10秒检查一次
    }

    // 停止监控
    stopMonitoring() {
        if (this.monitorInterval) {
            clearInterval(this.monitorInterval);
            this.monitorInterval = null;
        }
    }

    // 等待连接恢复
    async waitForConnection(timeout = 30000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const check = () => {
                if (this.isConnected) {
                    resolve(true);
                    return;
                }

                if (Date.now() - startTime > timeout) {
                    reject(new Error('等待连接超时'));
                    return;
                }

                setTimeout(check, 1000);
            };

            check();
        });
    }
}

// 创建全局连接监控实例
window.connectionMonitor = new ConnectionMonitor();

// 页面加载完成后开始监控
document.addEventListener('DOMContentLoaded', function() {
    window.connectionMonitor.startMonitoring();
});

// 页面卸载时停止监控
window.addEventListener('beforeunload', function() {
    window.connectionMonitor.stopMonitoring();
});