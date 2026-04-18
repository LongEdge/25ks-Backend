# 部署指南

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.10 | 推荐 3.10 / 3.11 |
| MySQL | ≥ 8.0 | 可选，生产环境推荐 |
| Redis | ≥ 6.0 | 必需，任务状态缓存 |
| uv | 最新版 | 推荐用 uv 安装依赖 |

## 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/LongEdge/25ks-Backend.git
cd 25ks-Backend
```

### 2. 安装依赖

```bash
# 推荐使用 uv
pip install uv
uv sync

# 或传统方式
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# 数据库（SQLite 默认，开发用）
DATABASE_URL=sqlite:///./app.db

# 或使用 MySQL
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/25ks

# JWT 密钥（生产环境务必修改）
SECRET_KEY=your-super-secret-key-change-in-production

# 智谱 AI（GLM-4）
AI_API_KEY=your-zhipu-api-key
AI_BASE_URL=https://api.zhipu.cn/v1

# 智谱媒体（CogView/CogVideo）
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# Redis
REDIS_URL=localhost:6379
REDIS_KEY=

# 阿里云 OSS（可选）
ALIYUN_ACCESS_KEY_ID=your-key-id
ALIYUN_ACCESS_KEY_SECRET=your-secret
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=your-bucket
ALIYUN_OSS_DOMAIN=https://your-bucket.oss-cn-hangzhou.aliyuncs.com

# 知识图谱 CSV（可选）
KG_CSV_PATH=resources/out_v2_chinese_teaching.csv
EOF
```

### 4. 初始化数据库

```bash
python init_db.py
```

### 5. 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger 文档。

---

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 构建与运行

```bash
# 构建镜像
docker build -t 25ks-backend:latest .

# 运行（需要 MySQL 和 Redis）
docker run -d -p 8000:8000 \
  --env-file .env \
  25ks-backend:latest
```

### Docker Compose（推荐）

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - mysql
      - redis
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: 25ks
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

---

## 生产环境配置

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 静态文件（如果有）
    location /static/ {
        alias /app/static/;
    }

    # API 代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd 服务

```ini
[Unit]
Description=25ks-Backend AI Teacher Assistant
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/25ks-Backend
Environment="PATH=/opt/25ks-Backend/.venv/bin"
ExecStart=/opt/25ks-Backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable 25ks-backend
sudo systemctl start 25ks-backend
sudo systemctl status 25ks-backend
```

---

## 外部服务申请

### 智谱 AI API

1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册账号并完成认证
3. 获取 API Key
4. 开通以下模型：
   - `glm-4-flash` 或 `glm-4`（教案/题库生成）
   - `cogview-3-flash`（图像生成）
   - `cogvideox-flash`（视频生成）

### 阿里云 OSS

1. 开通对象存储 OSS 服务
2. 创建 Bucket（建议与函数计算同区域）
3. 创建 AccessKey（RAM 子用户推荐）
4. 配置 Bucket 跨域规则

---

## 目录权限

```bash
# 创建必要的目录
mkdir -p uploads logs

# 设置权限
chmod 755 uploads
chmod 755 logs
```

---

## 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/status/ping

# 预期返回
{"status":"ok","message":"AI辅助教师备课系统API服务正常运行"}
```
