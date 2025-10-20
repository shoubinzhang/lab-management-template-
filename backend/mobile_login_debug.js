// 移动端登录调试工具
console.log('=== 移动端登录调试工具已加载 ===');

// 1. 显示当前网络环境信息
function showNetworkInfo() {
    const currentHost = window.location.hostname;
    const currentProtocol = window.location.protocol;
    const currentPort = window.location.port;
    const fullPath = window.location.href;
    
    console.log('=== 当前网络环境信息 ===');
    console.log('主机名:', currentHost);
    console.log('协议:', currentProtocol);
    console.log('端口:', currentPort || '默认');
    console.log('完整URL:', fullPath);
    console.log('用户代理:', navigator.userAgent);
    console.log('浏览器语言:', navigator.language);
    console.log('=== 网络环境信息结束 ===');
}

// 2. 测试API连接
async function testApiConnections() {
    console.log('=== 开始API连接测试 ===');
    
    const potentialApiUrls = [
        `${window.location.protocol}//${window.location.hostname}:8000`,
        'http://172.30.81.103:8000',
        'http://localhost:8000',
        'http://127.0.0.1:8000'
    ];
    
    for (const apiUrl of potentialApiUrls) {
        try {
            console.log(`测试API地址: ${apiUrl}`);
            const startTime = performance.now();
            const response = await fetch(`${apiUrl}/health`, { 
                timeout: 2000,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const endTime = performance.now();
            
            console.log(`测试结果: 状态码=${response.status}, 耗时=${endTime - startTime}ms`);
            
            if (response.ok) {
                const data = await response.json();
                console.log(`响应数据:`, data);
                console.log(`✓ ${apiUrl} - 连接成功`);
            } else {
                console.log(`✗ ${apiUrl} - 连接失败，状态码: ${response.status}`);
            }
        } catch (error) {
            console.log(`✗ ${apiUrl} - 连接异常:`, error.message);
        }
    }
    
    console.log('=== API连接测试结束 ===');
}

// 3. 模拟登录测试
async function simulateLogin(username, password) {
    console.log('=== 开始模拟登录测试 ===');
    console.log(`用户名: ${username}`);
    
    try {
        // 先尝试使用当前主机名构建API地址
        const apiUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
        const loginUrl = `${apiUrl}/api/auth/login`;
        
        console.log(`登录API地址: ${loginUrl}`);
        
        const startTime = performance.now();
        const response = await fetch(loginUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        const endTime = performance.now();
        
        console.log(`登录请求完成，状态码: ${response.status}, 耗时: ${endTime - startTime}ms`);
        
        if (response.ok) {
            const data = await response.json();
            console.log('登录成功！响应数据:', data);
            console.log(`用户角色: ${data.user.role}`);
            
            // 测试localStorage可用性
            try {
                localStorage.setItem('test_token', data.access_token.substring(0, 10) + '...');
                console.log('localStorage测试成功');
                localStorage.removeItem('test_token');
            } catch (storageError) {
                console.log('localStorage测试失败:', storageError.message);
            }
            
            // 显示模拟重定向信息
            const redirectUrl = `${window.location.protocol}//${window.location.hostname}:3000`;
            console.log(`模拟重定向地址: ${redirectUrl}`);
        } else {
            const errorText = await response.text();
            console.log('登录失败:', errorText);
        }
    } catch (error) {
        console.log('登录请求异常:', error.message);
    }
    
    console.log('=== 模拟登录测试结束 ===');
}

// 4. 生成调试按钮并添加到页面
function addDebugTools() {
    const debugDiv = document.createElement('div');
    debugDiv.style.position = 'fixed';
    debugDiv.style.bottom = '20px';
    debugDiv.style.left = '20px';
    debugDiv.style.zIndex = '9999';
    debugDiv.style.background = 'rgba(0,0,0,0.8)';
    debugDiv.style.padding = '10px';
    debugDiv.style.borderRadius = '8px';
    debugDiv.style.color = 'white';
    debugDiv.style.fontFamily = 'monospace';
    debugDiv.style.fontSize = '12px';
    debugDiv.style.maxWidth = '200px';
    
    const networkBtn = document.createElement('button');
    networkBtn.textContent = '显示网络信息';
    networkBtn.onclick = showNetworkInfo;
    networkBtn.style.display = 'block';
    networkBtn.style.width = '100%';
    networkBtn.style.marginBottom = '5px';
    networkBtn.style.padding = '5px';
    networkBtn.style.backgroundColor = '#28a745';
    networkBtn.style.color = 'white';
    networkBtn.style.border = 'none';
    networkBtn.style.borderRadius = '4px';
    networkBtn.style.cursor = 'pointer';
    
    const testBtn = document.createElement('button');
    testBtn.textContent = '测试API连接';
    testBtn.onclick = testApiConnections;
    testBtn.style.display = 'block';
    testBtn.style.width = '100%';
    testBtn.style.marginBottom = '5px';
    testBtn.style.padding = '5px';
    testBtn.style.backgroundColor = '#007bff';
    testBtn.style.color = 'white';
    testBtn.style.border = 'none';
    testBtn.style.borderRadius = '4px';
    testBtn.style.cursor = 'pointer';
    
    const loginBtn = document.createElement('button');
    loginBtn.textContent = '模拟登录';
    loginBtn.onclick = () => simulateLogin('admin', 'admin123');
    loginBtn.style.display = 'block';
    loginBtn.style.width = '100%';
    loginBtn.style.marginBottom = '5px';
    loginBtn.style.padding = '5px';
    loginBtn.style.backgroundColor = '#ffc107';
    loginBtn.style.color = 'black';
    loginBtn.style.border = 'none';
    loginBtn.style.borderRadius = '4px';
    loginBtn.style.cursor = 'pointer';
    
    const hideBtn = document.createElement('button');
    hideBtn.textContent = '隐藏';
    hideBtn.onclick = () => debugDiv.style.display = 'none';
    hideBtn.style.display = 'block';
    hideBtn.style.width = '100%';
    hideBtn.style.padding = '5px';
    hideBtn.style.backgroundColor = '#dc3545';
    hideBtn.style.color = 'white';
    hideBtn.style.border = 'none';
    hideBtn.style.borderRadius = '4px';
    hideBtn.style.cursor = 'pointer';
    
    debugDiv.appendChild(networkBtn);
    debugDiv.appendChild(testBtn);
    debugDiv.appendChild(loginBtn);
    debugDiv.appendChild(hideBtn);
    
    document.body.appendChild(debugDiv);
    
    console.log('调试工具已添加到页面底部');
}

// 页面加载完成后初始化调试工具
if (window.addEventListener) {
    window.addEventListener('load', addDebugTools);
} else if (window.attachEvent) {
    window.attachEvent('onload', addDebugTools);
}

// 导出函数供外部调用（如果需要）
window.MobileLoginDebug = {
    showNetworkInfo,
    testApiConnections,
    simulateLogin
};