# 实验室管理系统生产部署指南

## 概述

本指南详细说明如何将实验室管理系统部署到生产环境，支持手机和电脑访问，具备高可用性、安全性和可扩展性。

## 系统架构

```
[用户设备] → [Nginx负载均衡] → [前端容器] → [后端API容器] → [数据库容器]
                    ↓
               [SSL证书]
                    ↓
            [Redis缓存] + [监控系统]
```

## 部署前准备

### 1. 服务器要求

**最低配置:**
- CPU: 2核心
- 内存: 4GB RAM
- 存储: 50GB SSD
- 网络: 10Mbps带宽

**推荐配置:**
- CPU: 4核心
- 内存: 8GB RAM
- 存储: 100GB SSD
- 网络: 100Mbps带宽

### 2. 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 域名和DNS解析
- SSL证书

### 3. 域名配置

配置以下域名解析:
- `yourdomain.com` → 服务器IP
- `www.yourdomain.com` → 服务器IP
- `m.yourdomain.com` → 服务器IP (移动端优化)

## 部署步骤

### 第一步: 克隆项目

```bash
git clone <your-repository-url>
cd lab-management-app
```

### 第二步: 配置环境变量

```bash
# 复制生产环境配置模板
cp .env.production .env

# 编辑环境变量
vim .env
```

**重要配置项:**

```bash
# 数据库配置 - 请使用强密码
POSTGRES_PASSWORD=your_secure_database_password_here
REDIS_PASSWORD=your_secure_redis_password_here

# JWT密钥 - 请生成强密钥
JWT_SECRET_KEY=your_super_secure_jwt_secret_key

# 域名配置
REACT_APP_API_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 监控配置
GRAFANA_PASSWORD=your_secure_grafana_password
```

### 第三步: SSL证书配置

#### 选项A: 使用Let's Encrypt (推荐)

```bash
# 安装certbot
sudo apt install certbot

# 获取SSL证书
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d m.yourdomain.com

# 复制证书到项目目录
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl
```

#### 选项B: 使用自签名证书 (仅测试)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### 第四步: 更新Nginx配置

编辑 `nginx/nginx.prod.conf`，将 `yourdomain.com` 替换为你的实际域名。

### 第五步: 构建和启动服务

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 第六步: 数据库初始化

```bash
# 进入后端容器
docker exec -it lab-management-backend-prod bash

# 运行数据库迁移
python -m alembic upgrade head

# 创建管理员用户
python scripts/create_admin.py
```

### 第七步: 验证部署

1. **访问网站**: https://yourdomain.com
2. **检查移动端**: https://m.yourdomain.com
3. **API健康检查**: https://yourdomain.com/api/health
4. **监控面板**: https://yourdomain.com:3001 (Grafana)

## 移动端优化

### PWA功能

系统已配置为PWA (Progressive Web App)，支持:

- **离线访问**: 缓存关键资源
- **添加到主屏幕**: 类似原生应用体验
- **推送通知**: 实时消息提醒
- **响应式设计**: 适配各种屏幕尺寸

### 移动端访问

用户可以通过以下方式访问:

1. **浏览器访问**: 直接访问 https://yourdomain.com
2. **专用移动域名**: https://m.yourdomain.com
3. **PWA安装**: 浏览器提示"添加到主屏幕"

## 安全配置

### 1. 防火墙设置

```bash
# 开放必要端口
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. SSL安全配置

- 强制HTTPS重定向
- HSTS安全头
- 现代SSL/TLS配置
- OCSP装订

### 3. 应用安全

- JWT令牌认证
- CORS跨域保护
- XSS防护
- CSRF保护
- 输入验证和清理

## 监控和维护

### 1. 日志管理

```bash
# 查看应用日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx

# 查看系统资源
docker stats
```

### 2. 数据库备份

系统已配置自动备份:

- **备份频率**: 每天凌晨2点
- **保留期限**: 30天
- **备份位置**: `./backups/`

手动备份:

```bash
# 手动执行备份
docker exec lab-management-backup /backup.sh

# 查看备份文件
ls -la backups/
```

### 3. 监控面板

访问 Grafana 监控面板:

- **URL**: https://yourdomain.com:3001
- **用户名**: admin
- **密码**: 在 `.env` 文件中的 `GRAFANA_PASSWORD`

监控指标包括:

- 系统资源使用率
- 应用性能指标
- 数据库连接状态
- API响应时间
- 错误率统计

## 扩展和优化

### 1. 负载均衡

如需处理更高负载，可以:

```bash
# 增加后端实例
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# 增加前端实例
docker-compose -f docker-compose.prod.yml up -d --scale frontend=2
```

### 2. 数据库优化

- 配置连接池
- 启用查询缓存
- 定期数据库维护
- 索引优化

### 3. CDN配置

建议使用CDN加速静态资源:

- 图片和文件上传
- CSS和JavaScript文件
- 字体文件

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看详细日志
   docker-compose -f docker-compose.prod.yml logs container_name
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker exec lab-management-db-prod pg_isready
   ```

3. **SSL证书问题**
   ```bash
   # 检查证书有效性
   openssl x509 -in nginx/ssl/fullchain.pem -text -noout
   ```

4. **性能问题**
   ```bash
   # 查看资源使用
   docker stats
   htop
   ```

### 紧急恢复

```bash
# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 从备份恢复数据库
docker exec -i lab-management-db-prod psql -U lab_user -d lab_management < backups/latest_backup.sql

# 重新启动服务
docker-compose -f docker-compose.prod.yml up -d
```

## 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose -f docker-compose.prod.yml build

# 滚动更新
docker-compose -f docker-compose.prod.yml up -d
```

## 联系支持

如遇到部署问题，请提供:

1. 错误日志
2. 系统配置信息
3. 部署环境详情
4. 复现步骤

---

**注意**: 请确保在生产环境中使用强密码，定期更新系统和依赖，监控安全漏洞。