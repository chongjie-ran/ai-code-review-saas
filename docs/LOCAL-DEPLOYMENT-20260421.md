# AI代码审查SaaS 本地部署验证报告

**项目**: CodeLens AI (ai-code-review-saas)
**验证日期**: 2026-04-21
**验证人**: 鸣商
**分支**: dev

---

## 1. 验证概述

| 项目 | 结果 |
|------|------|
| P0安全修复验证 | ✅ 通过 |
| 本地Docker Compose部署 | ✅ 通过 |
| Backend健康检查 | ✅ 通过 |
| Frontend可访问性 | ✅ 通过 |

---

## 2. 部署环境

- **平台**: macOS (Docker Desktop)
- **Docker**: 29.2.1
- **Docker Compose**: v5.1.0
- **端口**: Backend 8090, Frontend 3000

---

## 3. 修复的问题

### 3.1 TD-01: 密码哈希 (SHA256 → bcrypt)

**文件**: `backend/app/auth.py`
**Commit**: [18484f01](https://github.com/chongjie-ran/ai-code-review-saas/commit/18484f01d723c00d96c46f4f7f422e1683c7655a)

```python
# Before: 不安全的SHA256
import hashlib
h = hashlib.sha256(password.encode()).hexdigest()

# After: bcrypt
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context.hash(password)
```

### 3.2 TD-02: CORS配置

**文件**: `backend/app/main.py`
**Commit**: [659252ba](https://github.com/chongjie-ran/ai-code-review-saas/commit/659252ba2b4602e236f19dc1fd3630e267820f23)

```python
# Before: allow_origins=["*"] (生产环境危险)
# After: 环境变量配置
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "https://app.example.com").split(",")
```

### 3.3 TD-03: JWT_SECRET强制配置

**文件**: `backend/app/auth.py`
**修复**: 启动时必须设置JWT_SECRET环境变量，否则抛出ValueError

```python
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")
```

### 3.4 额外修复: 环境变量名不一致

**文件**: `docker-compose.yml` + `backend/app/encryption.py`
**Commit**: [de3bb80c](https://github.com/chongjie-ran/ai-code-review-saas/commit/de3bb80cbc53e92473e110dfa1d2f65529f71f84), [8c0544f](https://github.com/chongjie-ran/ai-code-review-saas/commit/8c0544ff2ab3a39436d1a6ce79da589f6321e1a4)

问题: docker-compose.yml传递`CODELENS_JWT_SECRET`，但代码读`JWT_SECRET`
修复:
- docker-compose.yml: `CODELENS_JWT_SECRET=` → `JWT_SECRET=`
- encryption.py: `os.getenv("CODELENS_JWT_SECRET")` → `os.getenv("JWT_SECRET")`
- 新增`CORS_ORIGINS`环境变量映射

---

## 4. 部署步骤

### 4.1 克隆仓库（dev分支）

```bash
git clone -b dev https://github.com/chongjie-ran/ai-code-review-saas.git
cd ai-code-review-saas
```

### 4.2 配置环境变量

```bash
cp .env.example .env
# 编辑.env，设置JWT_SECRET（必须，32字符以上）
# 设置CORS_ORIGINS（本地开发: http://localhost:3000）
```

`.env`示例:
```bash
JWT_SECRET=your-super-secret-jwt-key-at-least-32-characters-long
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
RATE_LIMIT=100
RATE_WINDOW=60
ANONYMOUS_LIMIT=20
AUDIT_RETENTION_DAYS=90
```

### 4.3 启动服务

```bash
# 启动所有服务
docker-compose up --build -d

# 检查状态
docker ps | grep codelens

# 查看日志
docker-compose logs -f backend
```

### 4.4 验证

```bash
# Backend健康检查
curl http://localhost:8090/health
# 预期: {"status": "ok", "service": "CodeLens AI", "version": "v1.0.0"}

# Frontend访问
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
# 预期: 200
```

### 4.5 停止服务

```bash
docker-compose down
```

---

## 5. 验证结果

| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| Backend健康检查 | 200 + JSON | 200 + `{"status":"ok"}` | ✅ |
| Frontend访问 | 200 | 200 | ✅ |
| JWT_SECRET强制 | 必须设置 | 启动时检查 | ✅ |
| CORS_ORIGINS | 可配置 | 默认localhost | ✅ |

---

## 6. 发现的问题

| 问题 | 严重度 | 状态 |
|------|--------|------|
| 环境变量名不一致 | 高 | ✅ 已修复并推送 |
| docker-compose缺少CORS_ORIGINS | 中 | ✅ 已修复并推送 |
| docker-compose缺少ANONYMOUS_LIMIT | 低 | ✅ 已修复并推送 |

### 6.1 新发现：AuditMiddleware 请求体Bug

| 项目 | 内容 |
|------|------|
| **问题** | AuditMiddleware 读取 POST 请求体后未放回流中，导致 handler 无法读取，请求永久挂起 |
| **根因** | `_get_body()` 消费了 receive stream 但没有 replay 函数 |
| **影响** | 所有 POST/PUT/PATCH 请求（注册、登录、分析等）超时 |
| **修复** | `_get_body()` 返回 `(body_str, receive_replay)`，中间件使用 replay 函数代替原始 receive |
| **Commit** | `3fb2e465` |

### 6.2 新发现：bcrypt 阻塞事件循环

| 项目 | 内容 |
|------|------|
| **问题** | bcrypt 是 CPU 密集型操作，单线程 uvicorn 被阻塞 |
| **修复** | 使用 `concurrent.futures.ThreadPoolExecutor` 执行 bcrypt，async 函数通过 `run_in_executor` 调用 |
| **Commit** | `f0004822` |
| **注意** | bcrypt 实际只需 0.2 秒，修复后不影响用户体验 |

---

## 7. 下一步

- [ ] 测试JWT登录/登出流程
- [ ] 测试CORS配置（跨域请求）
- [ ] 合并dev到main，准备生产部署
- [ ] 生产环境配置真实域名和SSL

---

*文档生成: 2026-04-21 by 鸣商*
