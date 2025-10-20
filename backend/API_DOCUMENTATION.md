# 实验室管理系统 API 接口文档

## 基础信息

- **基础URL**: `http://127.0.0.1:8000`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

## 认证接口

### 用户登录
```http
POST /api/auth/login
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

## 使用记录接口

### 1. 获取使用记录列表

```http
GET /api/usage-records/
```

**查询参数**:
- `skip` (int, 可选): 跳过记录数，默认 0
- `limit` (int, 可选): 限制记录数，默认 100
- `item_type` (string, 可选): 物品类型筛选 ("reagent" 或 "consumable")
- `user_id` (int, 可选): 用户ID筛选

**响应**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "item_type": "reagent",
    "item_id": 1,
    "item_name": "硫酸",
    "quantity_used": 100.0,
    "unit": "ml",
    "purpose": "实验用途",
    "used_at": "2025-01-18T10:30:00Z",
    "notes": "通过申请 #1 批准使用",
    "created_at": "2025-01-18T10:30:00Z"
  }
]
```

### 2. 获取当前用户的使用记录

```http
GET /api/usage-records/my
```

**需要认证**: Bearer Token

**查询参数**:
- `skip` (int, 可选): 跳过记录数，默认 0
- `limit` (int, 可选): 限制记录数，默认 100

**响应**: 同上

### 3. 获取特定使用记录详情

```http
GET /api/usage-records/{record_id}
```

**需要认证**: Bearer Token

**路径参数**:
- `record_id` (int): 使用记录ID

**响应**:
```json
{
  "id": 1,
  "user_id": 1,
  "item_type": "reagent",
  "item_id": 1,
  "item_name": "硫酸",
  "quantity_used": 100.0,
  "unit": "ml",
  "purpose": "实验用途",
  "used_at": "2025-01-18T10:30:00Z",
  "notes": "通过申请 #1 批准使用",
  "created_at": "2025-01-18T10:30:00Z"
}
```

### 4. 获取使用统计数据

```http
GET /api/usage-records/stats
```

**需要认证**: Bearer Token

**响应**:
```json
{
  "total_records": 150,
  "by_item_type": {
    "reagent": 80,
    "consumable": 70
  },
  "by_user": {
    "1": 45,
    "2": 35,
    "3": 70
  },
  "recent_usage": [
    {
      "date": "2025-01-18",
      "count": 5
    }
  ]
}
```

## 申请管理接口

### 1. 创建申请

```http
POST /api/requests/
```

**需要认证**: Bearer Token

**请求体**:
```json
{
  "request_type": "reagent",
  "item_id": 1,
  "item_name": "硫酸",
  "quantity": 100.0,
  "unit": "ml",
  "purpose": "实验用途",
  "urgency": "normal"
}
```

**响应**:
```json
{
  "id": 1,
  "request_type": "reagent",
  "item_id": 1,
  "item_name": "硫酸",
  "quantity": 100.0,
  "unit": "ml",
  "purpose": "实验用途",
  "urgency": "normal",
  "status": "pending",
  "requester_id": 1,
  "created_at": "2025-01-18T10:00:00Z"
}
```

### 2. 获取申请列表

```http
GET /api/requests/
```

**需要认证**: Bearer Token

**查询参数**:
- `skip` (int, 可选): 跳过记录数
- `limit` (int, 可选): 限制记录数
- `status` (string, 可选): 状态筛选

**响应**:
```json
[
  {
    "id": 1,
    "request_type": "reagent",
    "item_id": 1,
    "item_name": "硫酸",
    "quantity": 100.0,
    "unit": "ml",
    "purpose": "实验用途",
    "urgency": "normal",
    "status": "pending",
    "requester_id": 1,
    "created_at": "2025-01-18T10:00:00Z"
  }
]
```

### 3. 批准申请

```http
POST /api/requests/{request_id}/approve
```

**需要认证**: Bearer Token (管理员权限)

**路径参数**:
- `request_id` (int): 申请ID

**请求体**:
```json
{
  "notes": "批准备注"
}
```

**响应**:
```json
{
  "message": "申请已批准",
  "request_id": 1,
  "usage_record_id": 1,
  "remaining_stock": 900.0
}
```

### 4. 拒绝申请

```http
POST /api/requests/{request_id}/reject
```

**需要认证**: Bearer Token (管理员权限)

**路径参数**:
- `request_id` (int): 申请ID

**请求体**:
```json
{
  "reason": "拒绝原因"
}
```

## 试剂管理接口

### 1. 获取试剂列表

```http
GET /api/reagents/
```

**查询参数**:
- `skip` (int, 可选): 跳过记录数
- `limit` (int, 可选): 限制记录数

**响应**:
```json
[
  {
    "id": 1,
    "name": "硫酸",
    "cas_number": "7664-93-9",
    "molecular_formula": "H2SO4",
    "molecular_weight": 98.08,
    "purity": "98%",
    "manufacturer": "国药集团",
    "supplier": "试剂供应商",
    "quantity": 1000.0,
    "unit": "ml",
    "location": "A1-01",
    "expiry_date": "2025-12-31",
    "safety_info": "强酸，腐蚀性",
    "storage_conditions": "阴凉干燥处",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-18T10:00:00Z"
  }
]
```

### 2. 获取试剂详情

```http
GET /api/reagents/{reagent_id}
```

**路径参数**:
- `reagent_id` (int): 试剂ID

**响应**: 同上单个试剂对象

## 耗材管理接口

### 1. 获取耗材列表

```http
GET /api/consumables/
```

**查询参数**:
- `skip` (int, 可选): 跳过记录数
- `limit` (int, 可选): 限制记录数

**响应**:
```json
[
  {
    "id": 1,
    "name": "移液器吸头",
    "specification": "1000μL",
    "brand": "Eppendorf",
    "model": "EP-1000",
    "quantity": 500,
    "unit": "个",
    "location": "B2-05",
    "supplier": "耗材供应商",
    "purchase_date": "2025-01-01",
    "expiry_date": "2026-01-01",
    "notes": "无菌包装",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-18T10:00:00Z"
  }
]
```

### 2. 获取耗材详情

```http
GET /api/consumables/{consumable_id}
```

**路径参数**:
- `consumable_id` (int): 耗材ID

**响应**: 同上单个耗材对象

## 用户管理接口

### 1. 获取用户信息

```http
GET /api/users/me
```

**需要认证**: Bearer Token

**响应**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "created_at": "2025-01-01T00:00:00Z"
}
```

## 错误响应

所有API在出错时返回统一格式的错误响应：

```json
{
  "detail": "错误描述信息"
}
```

### 常见状态码

- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未认证或认证失败
- `403` - 权限不足
- `404` - 资源不存在
- `422` - 请求数据验证失败
- `500` - 服务器内部错误

## 数据模型

### UsageRecord (使用记录)
```json
{
  "id": "integer",
  "user_id": "integer",
  "item_type": "string (reagent|consumable)",
  "item_id": "integer",
  "item_name": "string",
  "quantity_used": "float",
  "unit": "string",
  "purpose": "string",
  "used_at": "datetime",
  "notes": "string",
  "created_at": "datetime"
}
```

### Request (申请)
```json
{
  "id": "integer",
  "request_type": "string (reagent|consumable)",
  "item_id": "integer",
  "item_name": "string",
  "quantity": "float",
  "unit": "string",
  "purpose": "string",
  "urgency": "string (low|normal|high|urgent)",
  "status": "string (pending|approved|rejected)",
  "requester_id": "integer",
  "approver_id": "integer",
  "approved_at": "datetime",
  "notes": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 使用示例

### Python 示例

```python
import requests

# 登录获取token
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# 设置认证头
headers = {"Authorization": f"Bearer {token}"}

# 获取使用记录
usage_records = requests.get(
    "http://127.0.0.1:8000/api/usage-records/my",
    headers=headers
)

print(usage_records.json())
```

### JavaScript 示例

```javascript
// 登录获取token
const loginResponse = await fetch('${apiBaseUrl}/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const { access_token } = await loginResponse.json();

// 获取使用记录
const usageRecords = await fetch('${apiBaseUrl}/api/usage-records/my', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const records = await usageRecords.json();
console.log(records);
```

---

**文档版本**: v1.0
**最后更新**: 2025年1月18日