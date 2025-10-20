// 集成测试脚本 - 验证前后端连接是否正常
const axios = require('axios');
const WebSocket = require('ws');

console.log('=== 实验室管理应用集成测试 ===\n');

// 配置
const FRONTEND_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8001';

// 测试函数
async function runTests() {
    // 测试1: 检查前端服务器是否正常运行
    console.log('测试1: 检查前端服务器...');
    try {
        const frontendResponse = await axios.get(FRONTEND_URL, { timeout: 5000 });
        console.log(`✅ 前端服务器正常: ${frontendResponse.status} ${frontendResponse.statusText}`);
    } catch (error) {
        console.error('❌ 前端服务器访问失败:', error.message);
    }

    // 测试2: 检查后端API是否正常运行
    console.log('\n测试2: 检查后端API...');
    try {
        const backendResponse = await axios.get(`${BACKEND_URL}/docs`, { timeout: 5000 });
        console.log(`✅ 后端API正常: ${backendResponse.status} ${backendResponse.statusText}`);
    } catch (error) {
        console.error('❌ 后端API访问失败:', error.message);
    }

    // 测试3: 检查前端代理是否正常工作
    console.log('\n测试3: 检查前端代理...');
    try {
        const proxyResponse = await axios.get(`${FRONTEND_URL}/api/health`, { timeout: 5000 });
        console.log(`✅ 前端代理正常: ${proxyResponse.status} ${proxyResponse.statusText}`);
        console.log(`   后端健康状态: ${proxyResponse.data.status}`);
    } catch (error) {
        console.error('❌ 前端代理访问失败:', error.message);
        if (error.response) {
            console.error(`   响应状态: ${error.response.status}`);
        }
    }

    // 测试4: 检查WebSocket连接
    console.log('\n测试4: 检查WebSocket连接...');
    await testWebSocket();

    console.log('\n=== 测试完成 ===');
}

// WebSocket测试函数
function testWebSocket() {
    return new Promise((resolve) => {
        try {
            const ws = new WebSocket(`ws://localhost:8001/api/ws/notifications`);
            
            ws.on('open', () => {
                console.log('✅ WebSocket连接成功建立');
                ws.close();
                resolve();
            });
            
            ws.on('error', (error) => {
                console.error('❌ WebSocket连接失败:', error.message);
                resolve();
            });
            
            ws.on('close', () => {
                console.log('WebSocket连接已关闭');
            });
            
            // 设置超时
            setTimeout(() => {
                if (ws.readyState !== ws.CLOSED) {
                    console.error('❌ WebSocket连接超时');
                    ws.close();
                    resolve();
                }
            }, 5000);
        } catch (error) {
            console.error('❌ WebSocket测试异常:', error.message);
            resolve();
        }
    });
}

// 运行测试
runTests().catch(error => {
    console.error('测试过程中发生错误:', error);
});