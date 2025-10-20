# 域名和DNS配置指南

## 概述

本指南详细说明如何为实验室管理系统配置域名和DNS解析，确保系统可以通过自定义域名访问，并支持移动端优化。

## 域名规划

### 推荐域名结构

```
主域名: lab.yourdomain.com
移动端: m.lab.yourdomain.com
API接口: api.lab.yourdomain.com
监控面板: monitor.lab.yourdomain.com
```

或者使用主域名:

```
主域名: yourdomain.com
移动端: m.yourdomain.com
API接口: api.yourdomain.com
监控面板: monitor.yourdomain.com
```

## DNS记录配置

### 1. A记录配置

在你的DNS提供商控制面板中添加以下A记录:

| 主机名 | 类型 | 值 | TTL |
|--------|------|----|----- |
| @ | A | 你的服务器IP | 300 |
| www | A | 你的服务器IP | 300 |
| m | A | 你的服务器IP | 300 |
| api | A | 你的服务器IP | 300 |
| monitor | A | 你的服务器IP | 300 |

### 2. CNAME记录配置 (可选)

如果使用子域名:

| 主机名 | 类型 | 值 | TTL |
|--------|------|----|----- |
| lab | A | 你的服务器IP | 300 |
| www.lab | CNAME | lab.yourdomain.com | 300 |
| m.lab | CNAME | lab.yourdomain.com | 300 |

### 3. 安全记录配置

#### CAA记录 (证书颁发机构授权)

```
yourdomain.com. CAA 0 issue "letsencrypt.org"
yourdomain.com. CAA 0 issuewild "letsencrypt.org"
yourdomain.com. CAA 0 iodef "mailto:admin@yourdomain.com"
```

#### SPF记录 (如果发送邮件)

```
yourdomain.com. TXT "v=spf1 include:_spf.google.com ~all"
```

## 常见DNS提供商配置

### 1. 阿里云DNS

1. 登录阿里云控制台
2. 进入"云解析DNS"
3. 选择你的域名
4. 添加记录:
   ```
   记录类型: A
   主机记录: @
   解析路线: 默认
   记录值: 你的服务器IP
   TTL: 10分钟
   ```

### 2. 腾讯云DNS

1. 登录腾讯云控制台
2. 进入"DNS解析DNSPod"
3. 选择域名管理
4. 添加记录:
   ```
   主机记录: @
   记录类型: A
   线路类型: 默认
   记录值: 你的服务器IP
   TTL: 600
   ```

### 3. Cloudflare

1. 登录Cloudflare控制台
2. 选择你的域名
3. 进入DNS设置
4. 添加记录:
   ```
   Type: A
   Name: @
   IPv4 address: 你的服务器IP
   Proxy status: DNS only (灰色云朵)
   TTL: Auto
   ```

### 4. GoDaddy

1. 登录GoDaddy账户
2. 进入"我的产品" > "DNS"
3. 选择域名
4. 添加记录:
   ```
   类型: A
   主机: @
   指向: 你的服务器IP
   TTL: 1小时
   ```

## DNS验证

### 1. 使用命令行工具验证

```bash
# 检查A记录
nslookup yourdomain.com
dig yourdomain.com A

# 检查所有子域名
nslookup www.yourdomain.com
nslookup m.yourdomain.com
nslookup api.yourdomain.com

# 检查DNS传播
dig @8.8.8.8 yourdomain.com
dig @1.1.1.1 yourdomain.com
```

### 2. 在线DNS检查工具

- [DNS Checker](https://dnschecker.org/)
- [What's My DNS](https://www.whatsmydns.net/)
- [DNS Propagation Checker](https://www.dnswatch.info/)

### 3. 验证脚本

创建验证脚本 `scripts/check-dns.sh`:

```bash
#!/bin/bash

DOMAIN="yourdomain.com"
SERVER_IP="你的服务器IP"

echo "检查DNS解析..."

domains=("$DOMAIN" "www.$DOMAIN" "m.$DOMAIN" "api.$DOMAIN")

for domain in "${domains[@]}"; do
    echo "检查 $domain..."
    resolved_ip=$(dig +short "$domain" A | tail -n1)
    
    if [ "$resolved_ip" = "$SERVER_IP" ]; then
        echo "✓ $domain 解析正确: $resolved_ip"
    else
        echo "✗ $domain 解析错误: $resolved_ip (期望: $SERVER_IP)"
    fi
done
```

## 移动端优化配置

### 1. 移动端专用域名

配置 `m.yourdomain.com` 用于移动端访问:

- 优化的CSS和JavaScript
- 压缩的图片资源
- 简化的界面布局
- 更快的加载速度

### 2. 智能DNS解析

某些DNS提供商支持智能解析:

```
# 移动端用户解析到移动优化服务器
m.yourdomain.com (移动端线路) → 移动优化服务器IP
m.yourdomain.com (默认线路) → 主服务器IP
```

## SSL证书配置

### 1. 多域名证书

申请包含所有子域名的SSL证书:

```bash
certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    -d m.yourdomain.com \
    -d api.yourdomain.com \
    -d monitor.yourdomain.com
```

### 2. 通配符证书

申请通配符证书覆盖所有子域名:

```bash
certbot certonly --manual \
    --preferred-challenges dns \
    -d yourdomain.com \
    -d *.yourdomain.com
```

## 环境变量更新

更新 `.env` 文件中的域名配置:

```bash
# 域名配置
DOMAIN=yourdomain.com
WWW_DOMAIN=www.yourdomain.com
MOBILE_DOMAIN=m.yourdomain.com
API_DOMAIN=api.yourdomain.com
MONITOR_DOMAIN=monitor.yourdomain.com

# 前端API地址
REACT_APP_API_URL=https://yourdomain.com

# CORS允许的源
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://m.yourdomain.com
```

## Nginx配置更新

更新 `nginx/nginx.prod.conf` 中的域名:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    # ... 其他配置
}

server {
    listen 443 ssl http2;
    server_name m.yourdomain.com;
    # ... 移动端配置
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    # ... API配置
}
```

## 故障排除

### 1. DNS解析问题

**问题**: 域名无法解析
**解决方案**:
```bash
# 检查DNS配置
nslookup yourdomain.com

# 清除本地DNS缓存
# Windows
ipconfig /flushdns

# Linux
sudo systemctl restart systemd-resolved

# macOS
sudo dscacheutil -flushcache
```

### 2. DNS传播延迟

**问题**: DNS更改未生效
**解决方案**:
- 等待TTL时间过期
- 使用不同的DNS服务器测试
- 检查全球DNS传播状态

### 3. SSL证书域名不匹配

**问题**: 证书域名错误
**解决方案**:
```bash
# 检查证书包含的域名
openssl x509 -in nginx/ssl/fullchain.pem -text -noout | grep DNS

# 重新申请包含所有域名的证书
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d m.yourdomain.com
```

## 性能优化

### 1. CDN配置

使用CDN加速静态资源:

```
static.yourdomain.com → CDN节点
img.yourdomain.com → 图片CDN
```

### 2. 地理位置优化

配置不同地区的服务器:

```
# 国内用户
yourdomain.com (国内线路) → 国内服务器

# 海外用户
yourdomain.com (海外线路) → 海外服务器
```

## 监控和维护

### 1. DNS监控

设置DNS监控告警:

```bash
# 定期检查DNS解析
*/5 * * * * /path/to/check-dns.sh
```

### 2. 证书监控

监控SSL证书过期时间:

```bash
# 每天检查证书有效期
0 2 * * * /path/to/ssl-renew.sh
```

---

**注意**: DNS更改可能需要24-48小时才能在全球范围内完全传播。建议在低峰时段进行DNS更改。