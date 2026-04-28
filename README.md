# CodeLens AI

> AI代码审查SaaS - 专注AI生成代码的质量保障

**标语**: "让AI代码从风险到可信"

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Action-v1.1-blue?logo=github)](https://github.com/chongjie-ran/ai-code-review-action)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 核心功能

- 🔴 **逻辑错误检测** - 空指针、数组越界、类型不匹配
- 🔒 **安全漏洞扫描** - 注入风险、凭证泄露、命令执行
- 📉 **技术债务量化** - 重复代码、过时API、低可维护性
- 🤖 **GitHub Actions集成** - 一行配置，自动PR审查+评论

## 🤖 3步完成PR自动化审查

```yaml
# .github/workflows/codelens.yml
name: CodeLens AI Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: chongjie-ran/ai-code-review-action@v1.1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          codelens-api-key: ${{ secrets.CODELENS_API_KEY }}
          fail-on-high: true
```

添加 `CODELENS_API_KEY` secret 后，每次PR自动收到AI审查评论。

详细文档：https://github.com/chongjie-ran/ai-code-review-action

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

Python, JavaScript, TypeScript, Java, **Go**, **Rust**

## 🚀 v1.1 新功能

| 功能 | 描述 |
|------|------|
| **GitHub Actions** | 一行配置自动PR审查+评论 |
| **Go规则增强** | 8→18条规则 (+125%) |
| **Rust规则增强** | 7→20条规则 (+186%) |
| **bcrypt密码哈希** | SHA256升级为bcrypt |
| **CORS白名单** | 环境变量控制，禁止通配符 |
| **JWT强制配置** | 启动必填secret |
| **PDF报告导出** | `GET /api/v1/report/{session_id}?fmt=pdf` |
| **审计中间件** | 完整API操作记录 |
| **SSO / SAML** | 企业级单点登录 |
| **OIDC** | OpenID Connect协议支持 |
| **SOC2报告** | SOC2 Type II合规报告 |
| **Rate Limiting** | Token Bucket智能限流 |
| **Docker Compose** | 一键私有部署 |

详细部署文档: [docs/DEPLOY.md](docs/DEPLOY.md)

## 许可

MIT License

---

*CodeLens AI - 让AI代码从风险到可信*
