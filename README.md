# CodeLens AI

> AI代码审查SaaS - 专注AI生成代码的质量保障

**标语**: "让AI代码从风险到可信"

## 核心功能

- 🔴 **逻辑错误检测** - 空指针、数组越界、类型不匹配
- 🔒 **安全漏洞扫描** - 注入风险、凭证泄露、命令执行
- 📉 **技术债务量化** - 重复代码、过时API、低可维护性

## 快速开始

### Docker Compose (推荐)

```bash
git clone https://github.com/chongjie-ran/ai-code-review-saas.git
cd ai-code-review-saas
cp .env.example .env
# Edit .env and set JWT_SECRET
docker-compose up -d
```

访问 http://localhost:3000

### 手动运行

```bash
# Backend
cd backend
pip install -r requirements.txt
export JWT_SECRET="your-secret-key"
python -m uvicorn app.main:app --reload --port 8090

# Frontend
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## API

### 分析代码

```bash
curl -X POST http://localhost:8090/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "result = data.get(\"key\", None)\nif result: print(result.title())",
    "language": "python"
  }'
```

### 认证

```bash
# 注册
curl -X POST http://localhost:8090/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","name":"Test User"}'

# 登录
curl -X POST http://localhost:8090/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

## 技术栈

- **后端**: FastAPI + Python静态分析引擎
- **前端**: React + TypeScript
- **规则库**: 100+ AI代码专项规则
- **部署**: Docker Compose / Render / Railway

## 支持的语言

Python, JavaScript, TypeScript, Java, Go, Rust

## 🚀 Enterprise v1.0.0 新功能

| 功能 | 描述 |
|------|------|
| **SSO / SAML** | 企业级SAML 2.0单点登录 |
| **OIDC** | OpenID Connect协议支持 |
| **审计日志** | 完整API操作记录，可导出 |
| **SOC2报告** | SOC2 Type II合规报告 |
| **ISO27001报告** | ISO27001:2022合规报告 |
| **HIPAA报告** | HIPAA安全规则合规报告 |
| **Rate Limiting** | Token Bucket智能限流 |
| **AES-256加密** | 敏感数据静态加密 |
| **Docker Compose** | 一键私有部署 |

详细部署文档: [docs/DEPLOY.md](docs/DEPLOY.md)

## 许可

MIT License

---

*CodeLens AI - 让AI代码从风险到可信*
