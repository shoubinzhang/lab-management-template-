# 实验室管理系统部署文档

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (React)   │    │  后端 (FastAPI)  │    │ 数据库 (PostgreSQL)│
│   Port: 3000    │────│   Port: 8000    │────│   Port: 5432    │
│   Nginx Proxy   │    │   Gunicorn      │    │   数据持久化     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                         ┌─────────────────┐
                         │   监控系统       │
                         │   Sentry        │
                         │   日志收集       │
                         └─────────────────┘
```

## 环境要求

### 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **内存**: 最小 4GB，推荐 8GB+
- **存储**: 最小 20GB，推荐 50GB+
- **网络**: 稳定的互联网连接

### 软件依赖
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18.0+ (开发环境)
- **Python**: 3.9+ (开发环境)
- **PostgreSQL**: 14+ (生产环境)
- **Nginx**: 1.20+ (生产环境)

## 部署方式

### 1. Docker 容器化部署 (推荐)

#### 1.1 克隆项目
```bash
git clone <repository-url>
cd lab-management-app
```

#### 1.2 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

#### 1.3 启动服务
```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

#### 1.4 数据库初始化
```bash
# 进入后端容器
docker exec -it lab-backend bash

# 运行数据库迁移
python -m alembic upgrade head

# 创建初始管理员用户
python scripts/create_admin.py
```

### 2. 传统部署方式

#### 2.1 后端部署

##### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

##### 配置环境变量
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/labdb"
export SECRET_KEY="your-super-secret-key"
export ENVIRONMENT="production"
```

##### 启动服务
```bash
# 使用 Gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# 或使用 Uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 2.2 前端部署

##### 构建前端
```bash
cd frontend
npm install
npm run build
```

##### Nginx 配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 环境变量配置

### 后端环境变量
```bash
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/labdb

# JWT 配置
SECRET_KEY=your-super-secret-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 环境设置
ENVIRONMENT=production
DEBUG=false

# CORS 配置
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# 监控配置
SENTRY_DSN=your-sentry-dsn

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 前端环境变量
```bash
# API 基础URL
REACT_APP_API_BASE_URL=https://api.your-domain.com

# 环境标识
REACT_APP_ENVIRONMENT=production

# 监控配置
REACT_APP_SENTRY_DSN=your-frontend-sentry-dsn
```

## 数据库配置

### PostgreSQL 安装和配置

#### Ubuntu/Debian
```bash
# 安装 PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE labdb;
CREATE USER labuser WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE labdb TO labuser;
\q
```

#### Docker 方式
```bash
docker run -d \
  --name lab-postgres \
  -e POSTGRES_DB=labdb \
  -e POSTGRES_USER=labuser \
  -e POSTGRES_PASSWORD=your-password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:14
```

### 数据库迁移

```bash
# 初始化 Alembic
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

## SSL/HTTPS 配置

### Let's Encrypt 证书

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Nginx HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 监控和日志

### 系统监控

#### Prometheus + Grafana
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

### 应用监控

#### Sentry 配置
```python
# backend/app.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

### 日志管理

#### 日志配置
```python
# backend/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
            logging.StreamHandler()
        ]
    )
```

## 备份和恢复

### 数据库备份

```bash
#!/bin/bash
# backup.sh
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups"
DB_NAME="labdb"
DB_USER="labuser"

# 创建备份
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

### 数据恢复

```bash
# 恢复数据库
psql -U labuser -h localhost -d labdb < backup_file.sql
```

### 自动备份

```bash
# 添加到 crontab
0 2 * * * /path/to/backup.sh
```

## 性能优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_reagents_name ON reagents(name);
CREATE INDEX idx_experiments_created_at ON experiments(created_at);

-- 分析表统计信息
ANALYZE;
```

### 应用优化

```python
# 连接池配置
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### 前端优化

```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
};
```

## 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库状态
sudo systemctl status postgresql

# 检查连接
psql -U labuser -h localhost -d labdb

# 查看日志
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 2. API 服务无响应
```bash
# 检查进程
ps aux | grep uvicorn

# 检查端口
netstat -tlnp | grep 8000

# 查看日志
tail -f logs/app.log
```

#### 3. 前端页面无法加载
```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 检查配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

### 日志位置

- **应用日志**: `/var/log/lab-management/app.log`
- **Nginx 日志**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL 日志**: `/var/log/postgresql/postgresql-14-main.log`
- **系统日志**: `/var/log/syslog`

## 安全检查清单

- [ ] 更改默认密码和密钥
- [ ] 配置防火墙规则
- [ ] 启用 HTTPS
- [ ] 设置 CORS 白名单
- [ ] 配置 SQL 注入防护
- [ ] 启用访问日志
- [ ] 定期更新依赖包
- [ ] 配置备份策略
- [ ] 设置监控告警
- [ ] 进行安全扫描

## 维护计划

### 日常维护
- 检查系统资源使用情况
- 查看应用日志
- 监控数据库性能
- 检查备份状态

### 周期维护
- **每周**: 更新安全补丁
- **每月**: 清理日志文件，优化数据库
- **每季度**: 性能评估，容量规划
- **每年**: 安全审计，灾难恢复演练

## 联系信息

- **技术支持**: tech-support@lab-management.com
- **紧急联系**: +86-xxx-xxxx-xxxx
- **文档更新**: 请提交 Issue 或 Pull Request

---

**最后更新**: 2024年1月
**文档版本**: 1.0.0