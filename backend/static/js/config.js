// 配置文件 - 统一管理API基础URL和其他配置项
const AppConfig = {
  // API基础URL配置
  api: {
    // 默认使用当前域名和协议，不硬编码端口号
    baseUrl: `${window.location.protocol}//${window.location.host}`,
    // 请求超时时间（毫秒）
    timeout: 5000,
    // 最大重试次数
    maxRetries: 3,
    // 重试间隔（毫秒）
    retryInterval: 1000
  },
  
  // 应用相关配置
  app: {
    // 应用名称
    name: '实验室管理系统',
    // 版本号
    version: '1.0.0',
    // 调试模式
    debug: true
  },
  
  // 功能开关
  features: {
    // 设备管理
    devices: true,
    // 试剂管理
    reagents: true,
    // 耗材管理
    consumables: true,
    // 扫码功能
    scan: true,
    // 预约功能
    reservations: true,
    // 维护功能
    maintenance: true
  },
  
  // 获取API完整URL
  getApiUrl(endpoint) {
    // 确保endpoint不以/开头
    if (endpoint && endpoint.startsWith('/')) {
      endpoint = endpoint.substring(1);
    }
    return `${this.api.baseUrl}/api/${endpoint}`;
  },
  
  // 日志记录函数
  log(message, level = 'info') {
    if (this.app.debug) {
      console[level]('[AppConfig]', message);
    }
  }
};

// 环境检测和适配
(function() {
  // 检测当前环境并根据需要调整配置
  const hostname = window.location.hostname;
  const port = window.location.port;
  
  // 开发环境检测 - 修复手机访问问题
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '172.30.81.97') {
    // 后端API服务器运行在端口8000，所以强制使用端口8000
    AppConfig.api.baseUrl = `${window.location.protocol}//172.30.81.97:8000`;
  }
  
  // 打印配置信息
  AppConfig.log(`当前API基础URL: ${AppConfig.api.baseUrl}`, 'info');
})();

// 导出配置对象，兼容模块化和非模块化环境
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
  module.exports = AppConfig;
} else {
  window.AppConfig = AppConfig;
}