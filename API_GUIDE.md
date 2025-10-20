# 实验室管理系统 API 使用指南

## 概述

实验室管理系统提供了完整的 RESTful API，支持用户管理、试剂管理、耗材管理、实验记录和设备管理等功能。

**基础信息**:
- **Base URL**: `http://localhost:8000` (开发环境) / `https://api.lab-management.com` (生产环境)
- **API 版本**: v1.0.0
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 快速开始

### 1. 获取访问令牌

```bash
# 用户登录
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@lab.com",
    "role": "admin"
  }
}
```

### 2. 使用访问令牌

```bash
# 在后续请求中包含 Authorization 头
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 认证和授权

### JWT Token 认证

所有受保护的 API 端点都需要在请求头中包含有效的 JWT token：

```
Authorization: Bearer <your-jwt-token>
```

### 用户角色

- **admin**: 系统管理员，拥有所有权限
- **researcher**: 研究员，可以管理实验和查看数据
- **user**: 普通用户，只能查看基本信息

## API 端点详解

### 用户管理 API

#### 用户注册

```http
POST /auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@lab.com",
  "password": "securepassword",
  "role": "user"
}
```

**响应**:
```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@lab.com",
  "role": "user",
  "created_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

#### 用户登录

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

#### 获取当前用户信息

```http
GET /api/users/me
Authorization: Bearer <token>
```

#### 获取所有用户 (管理员权限)

```http
GET /api/users
Authorization: Bearer <admin-token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `size`: 每页数量 (默认: 10)
- `role`: 按角色筛选
- `search`: 搜索用户名或邮箱

**示例**:
```bash
curl "http://localhost:8000/api/users?page=1&size=20&role=researcher&search=john"
```

### 试剂管理 API

#### 获取试剂列表

```http
GET /api/reagents
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `category`: 试剂类别
- `status`: 状态 (available, low_stock, expired)
- `search`: 搜索试剂名称或CAS号

**响应示例**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "氯化钠",
      "cas_number": "7647-14-5",
      "category": "无机盐",
      "quantity": 500,
      "unit": "g",
      "location": "A-1-01",
      "expiry_date": "2025-12-31",
      "status": "available",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 10,
  "pages": 15
}
```

#### 创建新试剂

```http
POST /api/reagents
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "硫酸铜",
  "cas_number": "7758-98-7",
  "category": "无机盐",
  "quantity": 250,
  "unit": "g",
  "location": "B-2-05",
  "expiry_date": "2025-06-30",
  "supplier": "化学试剂公司",
  "batch_number": "CU2024001",
  "safety_notes": "避免接触皮肤，使用时佩戴手套"
}
```

#### 更新试剂信息

```http
PUT /api/reagents/{reagent_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity": 200,
  "location": "B-2-06"
}
```

#### 删除试剂

```http
DELETE /api/reagents/{reagent_id}
Authorization: Bearer <token>
```

### 耗材管理 API

#### 获取耗材列表

```http
GET /api/consumables
Authorization: Bearer <token>
```

#### 创建耗材记录

```http
POST /api/consumables
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "移液器吸头",
  "type": "实验器具",
  "quantity": 1000,
  "unit": "个",
  "location": "C-1-01",
  "min_stock": 100,
  "supplier": "实验器材公司",
  "cost_per_unit": 0.5
}
```

### 实验记录 API

#### 获取实验记录

```http
GET /api/experiments
Authorization: Bearer <token>
```

**查询参数**:
- `date_from`: 开始日期 (YYYY-MM-DD)
- `date_to`: 结束日期 (YYYY-MM-DD)
- `researcher`: 研究员ID
- `status`: 实验状态 (planned, in_progress, completed, cancelled)

#### 创建实验记录

```http
POST /api/experiments
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "蛋白质纯化实验",
  "description": "使用亲和层析法纯化目标蛋白质",
  "researcher_id": 2,
  "start_date": "2024-01-20",
  "expected_end_date": "2024-01-25",
  "reagents_used": [
    {
      "reagent_id": 1,
      "quantity_used": 10,
      "unit": "ml"
    }
  ],
  "equipment_used": ["HPLC-001", "离心机-002"],
  "protocol": "按照标准蛋白质纯化流程进行..."
}
```

#### 更新实验状态

```http
PATCH /api/experiments/{experiment_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "completed",
  "results": "成功纯化得到95%纯度的目标蛋白质",
  "notes": "实验过程顺利，无异常情况"
}
```

### 设备管理 API

#### 获取设备列表

```http
GET /api/equipment
Authorization: Bearer <token>
```

#### 创建设备记录

```http
POST /api/equipment
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "高效液相色谱仪",
  "model": "HPLC-2000",
  "serial_number": "HPLC2024001",
  "location": "实验室A",
  "status": "available",
  "purchase_date": "2023-06-15",
  "warranty_expiry": "2026-06-15",
  "maintenance_schedule": "每月第一周",
  "responsible_person": "张研究员"
}
```

#### 设备状态更新

```http
PATCH /api/equipment/{equipment_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "maintenance",
  "notes": "定期维护检查"
}
```

## 错误处理

### HTTP 状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 数据验证失败
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "details": {
      "field": "email",
      "issue": "邮箱格式不正确"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/users"
}
```

### 常见错误代码

- `INVALID_TOKEN`: JWT token 无效或过期
- `INSUFFICIENT_PERMISSIONS`: 权限不足
- `VALIDATION_ERROR`: 数据验证失败
- `RESOURCE_NOT_FOUND`: 资源不存在
- `DUPLICATE_RESOURCE`: 资源重复
- `BUSINESS_LOGIC_ERROR`: 业务逻辑错误

## 分页和排序

### 分页参数

所有列表 API 都支持分页：

```http
GET /api/reagents?page=2&size=20
```

### 排序参数

```http
GET /api/reagents?sort=name&order=asc
GET /api/experiments?sort=created_at&order=desc
```

**可排序字段**:
- `name`: 名称
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `expiry_date`: 过期时间 (试剂)
- `quantity`: 数量

## 搜索和筛选

### 全文搜索

```http
GET /api/reagents?search=氯化钠
GET /api/users?search=john@lab.com
```

### 高级筛选

```http
# 按类别筛选试剂
GET /api/reagents?category=无机盐&status=available

# 按日期范围筛选实验
GET /api/experiments?date_from=2024-01-01&date_to=2024-01-31

# 按状态筛选设备
GET /api/equipment?status=available&location=实验室A
```

## 批量操作

### 批量创建

```http
POST /api/reagents/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "items": [
    {
      "name": "试剂1",
      "cas_number": "123-45-6",
      "quantity": 100
    },
    {
      "name": "试剂2",
      "cas_number": "789-01-2",
      "quantity": 200
    }
  ]
}
```

### 批量更新

```http
PATCH /api/reagents/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "updates": [
    {
      "id": 1,
      "quantity": 150
    },
    {
      "id": 2,
      "location": "A-2-01"
    }
  ]
}
```

## 数据导入导出

### 导出数据

```http
# 导出试剂数据为 CSV
GET /api/reagents/export?format=csv
Authorization: Bearer <token>

# 导出实验记录为 Excel
GET /api/experiments/export?format=xlsx&date_from=2024-01-01
Authorization: Bearer <token>
```

### 导入数据

```http
POST /api/reagents/import
Authorization: Bearer <token>
Content-Type: multipart/form-data

# 上传 CSV 或 Excel 文件
```

## 实时通知

### WebSocket 连接

```javascript
// 建立 WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

// 发送认证信息
ws.onopen = function() {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
};

// 接收通知
ws.onmessage = function(event) {
  const notification = JSON.parse(event.data);
  console.log('收到通知:', notification);
};
```

### 通知类型

- `reagent_low_stock`: 试剂库存不足
- `reagent_expiring`: 试剂即将过期
- `equipment_maintenance`: 设备需要维护
- `experiment_completed`: 实验完成
- `system_alert`: 系统警告

## SDK 和示例代码

### Python SDK

```python
import requests
from typing import Dict, List, Optional

class LabManagementAPI:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        response = self.session.post(
            f'{self.base_url}/auth/login',
            json={'username': username, 'password': password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })
        return data
    
    def get_reagents(self, page: int = 1, size: int = 10, **filters) -> Dict:
        """获取试剂列表"""
        params = {'page': page, 'size': size, **filters}
        response = self.session.get(
            f'{self.base_url}/api/reagents',
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def create_reagent(self, reagent_data: Dict) -> Dict:
        """创建试剂"""
        response = self.session.post(
            f'{self.base_url}/api/reagents',
            json=reagent_data
        )
        response.raise_for_status()
        return response.json()

# 使用示例
api = LabManagementAPI('http://localhost:8000')
api.login('admin', 'password123')

# 获取试剂列表
reagents = api.get_reagents(category='无机盐', status='available')
print(f'找到 {reagents["total"]} 个试剂')

# 创建新试剂
new_reagent = api.create_reagent({
    'name': '氢氧化钠',
    'cas_number': '1310-73-2',
    'quantity': 500,
    'unit': 'g',
    'location': 'A-1-02'
})
print(f'创建试剂成功，ID: {new_reagent["id"]}')
```

### JavaScript SDK

```javascript
class LabManagementAPI {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = token;
  }

  async request(method, endpoint, data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (this.token) {
      options.headers.Authorization = `Bearer ${this.token}`;
    }

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async login(username, password) {
    const data = await this.request('POST', '/auth/login', {
      username,
      password,
    });
    this.token = data.access_token;
    return data;
  }

  async getReagents(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/reagents${queryString ? `?${queryString}` : ''}`;
    return this.request('GET', endpoint);
  }

  async createReagent(reagentData) {
    return this.request('POST', '/api/reagents', reagentData);
  }
}

// 使用示例
const api = new LabManagementAPI('http://localhost:8000');

(async () => {
  try {
    // 登录
    await api.login('admin', 'password123');
    console.log('登录成功');

    // 获取试剂列表
    const reagents = await api.getReagents({
      category: '无机盐',
      status: 'available',
      page: 1,
      size: 20
    });
    console.log(`找到 ${reagents.total} 个试剂`);

    // 创建新试剂
    const newReagent = await api.createReagent({
      name: '碳酸钠',
      cas_number: '497-19-8',
      quantity: 300,
      unit: 'g',
      location: 'A-1-03'
    });
    console.log(`创建试剂成功，ID: ${newReagent.id}`);
  } catch (error) {
    console.error('API 调用失败:', error.message);
  }
})();
```

## 测试环境

### 测试数据

系统提供了测试数据集，包含：
- 3个测试用户 (admin, researcher, user)
- 50个试剂记录
- 20个耗材记录
- 10个实验记录
- 5个设备记录

### 重置测试数据

```http
POST /api/test/reset
Authorization: Bearer <admin-token>
```

## API 版本控制

### 版本策略

- 使用语义化版本控制 (Semantic Versioning)
- 主要版本变更会破坏向后兼容性
- 次要版本添加新功能但保持向后兼容
- 补丁版本仅修复错误

### 版本指定

```http
# 在 URL 中指定版本
GET /api/v1/reagents

# 在请求头中指定版本
GET /api/reagents
API-Version: 1.0
```

## 限流和配额

### 请求限制

- **普通用户**: 100 请求/分钟
- **研究员**: 200 请求/分钟
- **管理员**: 500 请求/分钟

### 响应头

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## 支持和反馈

- **API 文档**: http://localhost:8000/docs (Swagger UI)
- **技术支持**: api-support@lab-management.com
- **问题反馈**: https://github.com/lab-management/issues
- **更新日志**: https://github.com/lab-management/releases

---

**文档版本**: 1.0.0  
**最后更新**: 2024年1月15日