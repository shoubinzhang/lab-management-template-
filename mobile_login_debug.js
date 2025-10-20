// 移动端登录调试工具
console.log('======= 移动端登录调试工具已加载 =======');

// 显示当前网络环境信息
function showNetworkInfo() {
    try {
        const networkInfo = {
            '当前URL': window.location.href,
            '主机名': window.location.hostname,
            '协议': window.location.protocol,
            '端口': window.location.port,
            'API_BASE_URL': API_BASE_URL,
            'userAgent': navigator.userAgent
        };
        
        console.log('网络环境信息:', networkInfo);
        
        // 在调试信息区域显示
        const debugInfo = document.querySelector('.debug-info');
        if (debugInfo) {
            const networkDetails = document.createElement('div');
            networkDetails.style.marginTop = '10px';
            networkDetails.innerHTML = '<strong>网络信息：</strong><br>' +
                `URL: ${networkInfo['当前URL']}<br>` +
                `主机名: ${networkInfo['主机名']}<br>` +
                `协议: ${networkInfo['协议']}<br>` +
                `端口: ${networkInfo['端口']}`;
            debugInfo.appendChild(networkDetails);
        }
    } catch (error) {
        console.error('显示网络信息失败:', error);
    }
}

// 测试API连接
async function testApiConnection() {
    try {
        console.log('开始测试API连接...');
        const startTime = Date.now();
        
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Accept': 'application/json',
            },
            timeout: 5000
        });
        
        const endTime = Date.now();
        const data = await response.json();
        
        console.log(`API连接测试成功！耗时: ${endTime - startTime}ms`, data);
        
        // 更新UI显示
        if (connStatus) {
            connStatus.textContent = `连接正常 (${endTime - startTime}ms)`;
        }
        
        return { success: true, responseTime: endTime - startTime, data };
    } catch (error) {
        console.error('API连接测试失败:', error);
        
        // 更新UI显示
        if (connStatus) {
            connStatus.textContent = '连接失败';
        }
        if (errorDetails) {
            errorDetails.textContent = error.message;
        }
        
        return { success: false, error: error.message };
    }
}

// 创建调试按钮
function createDebugButtons() {
    const loginContainer = document.querySelector('.login-container');
    if (!loginContainer) return;
    
    const debugDiv = document.createElement('div');
    debugDiv.className = 'debug-buttons';
    debugDiv.style.marginTop = '20px';
    debugDiv.style.display = 'flex';
    debugDiv.style.gap = '10px';
    debugDiv.style.flexDirection = 'column';
    
    const testBtn = document.createElement('button');
    testBtn.textContent = '测试API连接';
    testBtn.style.padding = '10px';
    testBtn.style.fontSize = '14px';
    testBtn.onclick = async () => {
        testBtn.disabled = true;
        testBtn.textContent = '测试中...';
        await testApiConnection();
        testBtn.disabled = false;
        testBtn.textContent = '测试API连接';
    };
    
    const infoBtn = document.createElement('button');
    infoBtn.textContent = '显示网络信息';
    infoBtn.style.padding = '10px';
    infoBtn.style.fontSize = '14px';
    infoBtn.onclick = showNetworkInfo;
    
    debugDiv.appendChild(testBtn);
    debugDiv.appendChild(infoBtn);
    loginContainer.appendChild(debugDiv);
}

// 页面加载完成后初始化调试工具
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            showNetworkInfo();
            createDebugButtons();
        }, 500);
    });
} else {
    setTimeout(() => {
        showNetworkInfo();
        createDebugButtons();
    }, 500);
}

console.log('======= 调试工具初始化完成 =======');