# InkAI — 全栈博客系统

基于 **FastAPI** 开发的全栈博客后端系统，集成 MySQL 持久化存储与 Redis 多级缓存，支持 Docker Compose 一键部署。

> 🏷️ 如果你在学习 FastAPI + Redis + Docker，这个项目可以作为参考。项目结构清晰，涵盖了后端开发中常见的业务场景。

---

## 功能概览

### 用户系统
- 注册 / 登录（bcrypt 密码哈希）
- JWT 身份认证与中间件鉴权
- GitHub OAuth 2.0 第三方登录
- IP 级别注册登录限流（防暴力破解）

### 文章系统
- 文章增删改查
- 多标签分类（Redis Set 实现标签文章检索）
- 缓存穿透保护：空值缓存 + SET NX 互斥锁

### 点赞与热榜
- Redis ZSet 维护文章热度排序
- Lua 脚本保证点赞与计数原子性
- 热榜前 10 实时查询

### 缓存架构（三级防护）
- **防穿透**：查询结果为空时缓存空标记，避免恶意请求穿透到数据库
- **防击穿**：缓存失效时通过 SET NX 互斥锁控制只有一个请求回源数据库
- **防雪崩**：缓存 TTL 加入随机偏移量，防止大批缓存同时过期

### 安全
- Content-Security-Policy、X-Frame-Options、HSTS 等安全头
- 用户操作频率限制（按 IP / 按用户 ID）
- 统一异常处理与错误码规范

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **Web 框架** | FastAPI |
| **数据库** | MySQL 8.0（PyMySQL + DBUtils 连接池） |
| **缓存** | Redis 7（连接池） |
| **认证** | JWT + bcrypt + OAuth 2.0 |
| **部署** | Docker + Docker Compose（Nginx → MySQL → Redis） |
| **前端** | HTML + CSS + HTMX（动态交互） |
| **工具** | uvicorn、httpx、python-dotenv |

---

## 项目结构

```
InkAI/
├── api/                      # 路由层
│   ├── articles.py           #   文章 REST 接口
│   ├── auth.py               #   GitHub OAuth 接口
│   ├── html_routes.py        #   HTMX 前端路由
│   ├── likes.py              #   点赞 REST 接口
│   ├── tags.py               #   标签检索接口
│   └── users.py              #   注册/登录接口
├── core/                     # 核心组件
│   ├── exceptions.py         #   统一异常定义
│   ├── get_user_authorization.py  # JWT 鉴权依赖
│   ├── rate_limit.py         #   频率限制
│   └── security.py           #   密码哈希 + JWT 签发/验证
├── frontend/                 # 静态前端
│   ├── index.html
│   └── style.css
├── models/                   # 数据模型
│   ├── article.py
│   └── user.py
├── repositories/             # 数据访问层（SQL + Redis）
│   ├── article_repo.py
│   ├── cache_repo.py
│   └── user_repo.py
├── services/                 # 业务逻辑层
│   ├── article_service.py
│   ├── auth_service.py
│   └── like_service.py
├── utils/
│   └── jwt.py                # JWT 编解码工具
├── test/                     # 测试
├── app.py                    # FastAPI 入口
├── config.py                 # 配置
├── database.py               # Redis 连接池
├── db.py                     # MySQL 连接池
├── docker-compose.yml        # 容器编排
├── Dockerfile                # 多阶段构建
├── init.sql                  # 数据库初始化脚本
└── requirements.txt
```

架构分层：

```
api/ (路由) → services/ (业务) → repositories/ (数据) → db.py / database.py (连接池)
                                                                ↓
                                                          MySQL / Redis
```

---

## 快速开始

### 前置要求

- Docker & Docker Compose

### 启动

```bash
# 1. 克隆仓库
git clone https://github.com/elysianx138/InkAI.git
cd InkAI

# 2. 配置环境变量（可选）
# cp .env.example .env  # 按需修改数据库密码、JWT 密钥等

# 3. 一键启动
docker compose up -d

# 4. 访问
# http://localhost:8000
```

启动后会自动创建 MySQL 数据库表（`init.sql`），无需手动导入。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | `root123` | MySQL root 密码 |
| `MYSQL_DATABASE` | `blog` | 数据库名 |
| `MYSQL_HOST` | `localhost` | MySQL 主机（Docker 内自动设为 mysql） |
| `REDIS_HOST` | `localhost` | Redis 主机（Docker 内自动设为 redis） |
| `JWT_SECRET` | `myblog_jwt_secret` | JWT 签名密钥 |
| `JWT_TOKEN_EXPIRE` | `3600` | Token 过期时间（秒） |
| `GITHUB_CLIENT_ID` | — | GitHub OAuth App ID |
| `GITHUB_CLIENT_SECRET` | — | GitHub OAuth App Secret |
| `GITHUB_REDIRECT_URI` | — | GitHub OAuth 回调地址 |

---

## API 概览

### REST API

| 方法 | 路径 | 说明 | 需要认证 |
|------|------|------|:--------:|
| POST | `/signup` | 注册 | 否 |
| POST | `/login` | 登录，返回 JWT | 否 |
| GET | `/me` | 获取当前用户信息 | 是 |
| POST | `/articles` | 创建文章 | 是 |
| DELETE | `/articles/{id}` | 删除文章 | 是（本人） |
| GET | `/articles/{id}` | 获取文章详情 | 否 |
| GET | `/articles/{id}/tags` | 获取文章标签 | 否 |
| GET | `/article/latest` | 获取最新文章 | 否 |
| GET | `/articles?tag=xxx` | 按标签检索文章 | 否 |
| POST | `/articles/{id}/likes` | 点赞 | 是 |
| GET | `/articles/{id}/likes` | 获取点赞数 | 否 |
| GET | `/articles/hot` | 获取热门文章 Top 10 | 否 |
| GET | `/auth/github/login` | GitHub OAuth 登录 URL | 否 |
| GET | `/auth/github/callback` | GitHub OAuth 回调 | 否 |
| GET | `/healthz` | 健康检查 | 否 |

### HTMX 前端路由(辅助开发)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/hx/home` | 首页 |
| GET | `/hx/login` | 登录页 |
| POST | `/hx/login` | 登录提交 |
| GET | `/hx/register` | 注册页 |
| POST | `/hx/register` | 注册提交 |
| GET | `/hx/articles/create` | 写文章页 |
| POST | `/hx/articles` | 发布文章 |
| GET | `/hx/articles/{id}` | 文章详情 |
| POST | `/hx/articles/{id}/likes` | 点赞 |
| GET | `/hx/articles/tag?tag=xxx` | 按标签搜索 |
| POST | `/hx/logout` | 退出登录 |

---

## 部分实现细节

### 点赞原子性

使用 Lua 脚本在一次 Redis 操作中同时完成点赞数自增和 ZSet 热度更新：

```lua
local likes = redis.call("INCR", KEYS[1])
redis.call("ZINCRBY", KEYS[2], 1, KEYS[3])
return likes
```

### 缓存穿透保护

```python
# 查缓存
data = redis.hgetall(cache_key)
if data:
    if "__NULL__" in data:     # 空标记命中
        raise NotFoundError()
    return data

# 互斥锁：防击穿
redis.set(lock_key, "1", nx=True, ex=10)

# 回源数据库
article = db.find(id)
if not article:
    redis.hset(cache_key, {"__NULL__": "1"})
    redis.expire(cache_key, 60 + random.randint(0, 60))
    raise NotFoundError()

# 设置缓存，TTL 随机化：防雪崩
redis.expire(cache_key, 300 + random.randint(0, 120))
```

### 频率限制

基于 Redis INCR + EXPIRE 实现滑动窗口限流，分别对注册（5次/分钟）、登录（3次/分钟）、文章发布（10次/6分钟）做限制，阻断恶意请求。

---

## 本地开发（无 Docker）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保 MySQL 和 Redis 已启动

# 3. 初始化数据库
mysql -u root -p < init.sql

# 4. 启动服务
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

---

## 测试

```bash
docker compose run --rm web pytest test/ -v
```

---

## 许可证

[MIT](LICENSE)

## 联系我!
如果你喜欢我的项目,不要忘记star⭐
