# CodeLens AI

> AI代码审查SaaS - 专注AI生成代码的质量保障

**标语**: "让AI代码从风险到可信"

## 核心功能

- 🔴 **逻辑错误检测** - 空指针、数组越界、类型不匹配
- 🔒 **安全漏洞扫描** - 注入风险、凭证泄露、命令执行
- 📉 **技术债务量化** - 重复代码、过时API、低可维护性

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```

### 前端

```bash
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
    "code": "password = \"secret123\"",
    "language": "python",
    "options": {"check_security": true, "check_logic": true, "check_debt": true}
  }'
```

### 健康检查

```bash
curl http://localhost:8090/health
```

## CI/CD集成

### GitHub Actions

```yaml
- name: CodeLens AI Scan
  uses: codelens-ai/action@v0.1
  with:
    api_key: ${{ secrets.CODELENS_API_KEY }}
    languages: python,javascript
```

## 技术栈

- **后端**: FastAPI + Python
- **前端**: React + Vite
- **规则引擎**: 100+ AI代码专项规则

## 路线图

- [ ] 支持更多语言 (Rust, C++)
- [ ] GitHub/GitLab 插件市场
- [ ] 团队协作功能
- [ ] 企业版SSO

---

*悟空开发 | 2026-04-17*
