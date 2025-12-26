# 实验室管理系统 (Lab Management System)

这是一个现代化的实验室管理系统，用于管理实验室设备、试剂、实验预约和用户权限等功能。系统采用前后端分离架构，提供直观的用户界面和完整的API支持。

## 功能特性

### 后端功能
- 用户认证与授权系统
- 实验室设备管理（CRUD操作）
- 试剂库存管理
- 实验预约系统
- 数据统计与报表
- RESTful API接口

### 前端功能
- 响应式用户界面
- 设备管理页面
- 试剂管理页面
- 实验预约功能
- 多语言支持
- PWA支持（离线使用）

## 技术栈

### 后端
- Python 3.10+
- Flask 2.0+
- SQLAlchemy ORM
- MySQL 8.0+
- Redis（可选，用于缓存）

### 前端
- React 18+
- Ant Design
- React Router 6+
- Redux Toolkit
- Axios

## 安装指南

### 前置要求
- Python 3.10 或更高版本
- Node.js 16 或更高版本
- MySQL 8.0 或更高版本

### 后端安装

1. 克隆仓库
```bash
git clone <repository-url>
cd lab-management-app
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装后端依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
创建 `.env` 文件并配置数据库连接等信息

5. 初始化数据库
```bash
python -m backend.db.init_db
```

### 前端安装

1. 进入前端目录
```bash
cd frontend
```

2. 安装前端依赖
```bash
npm install
```

## 使用说明

### 运行后端服务
```bash
# 在项目根目录
python -m backend.app
```

### 运行前端开发服务器
```bash
# 在frontend目录
npm start
```

### 构建前端生产版本
```bash
# 在frontend目录
npm run build
```

## API文档

后端API遵循RESTful设计规范，主要接口包括：
- `/api/auth/*` - 认证相关接口
- `/api/devices/*` - 设备管理接口
- `/api/reagents/*` - 试剂管理接口
- `/api/reservations/*` - 预约管理接口

详细API文档可在运行后端服务后访问 `/api/docs` 获取。

## 项目结构

```
lab-management-app/
├── backend/             # 后端代码
│   ├── app.py          # 应用入口
│   ├── config.py       # 配置文件
│   ├── routes/         # API路由
│   ├── models/         # 数据库模型
│   └── services/       # 业务逻辑
├── frontend/            # 前端代码
│   ├── public/         # 静态资源
│   ├── src/            # 源代码
│   │   ├── components/ # React组件
│   │   ├── pages/      # 页面组件
│   │   ├── hooks/      # 自定义钩子
│   │   └── services/   # API服务
│   └── package.json    # 前端依赖
├── requirements.txt    # 后端依赖
└── README.md           # 项目说明
```

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 许可证

[MIT](https://choosealicense.com/licenses/mit/)

## 联系方式

如有问题或建议，请联系项目维护者。
