# 使用官方 Node.js 镜像作为基础镜像
FROM node:16 AS build

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json 到容器内
COPY package*.json ./

# 安装依赖
RUN npm install --legacy-peer-deps

# 复制项目的所有文件到容器
COPY . .

# 构建前端项目
RUN npm run build

# 使用 Nginx 作为静态文件的服务器
FROM nginx:alpine

# 删除默认的 Nginx 配置
RUN rm -rf /usr/share/nginx/html/*

# 复制构建好的前端文件到 Nginx 服务目录
COPY --from=build /app/build /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 Nginx 服务
CMD ["nginx", "-g", "daemon off;"]
