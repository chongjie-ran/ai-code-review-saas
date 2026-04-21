# AI代码审查SaaS 发布后监控机制
> 版本：v1.0 | 日期：2026-04-21
> 负责人：真理（测试专家）
> 项目：https://github.com/chongjie-ran/ai-code-review-saas
> 当前版本：v1.0.0 (2026-04-17)

---

## 一、项目现状概述

### 1.1 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI + Python | 端口 8090 |
| 前端 | React + TypeScript | 端口 3000 (nginx) |
| 数据库 | SQLite (codelens.db + audit) | 本地文件存储 |
| 会话存储 | 内存/SQLite | 已有Redis配置（可选） |
| 指标收集 | Prometheus（可选配置） | 端口 9090 |
| 部署 | Docker Compose | 已内置 healthcheck |

### 1.2 已有监控基础设施

- ✅ `docker-compose.yml` 已配置 Prometheus 服务（注释状态）
- ✅ `docker-compose.yml` 已配置 Redis 服务（注释状态）
- ✅ 已有 `/health` 健康检查端点（`GET /health`）
- ✅ 已有 `AuditMiddleware`（自动记录所有API请求）
- ✅ 已有 `RateLimitMiddleware`（Token Bucket限流）
- ✅ GitHub Actions CI 已配置（`.github/workflows/ci.yml`）

---

## 二、生产环境监控方案

### 2.1 推荐监控工具选型

**方案A：轻量级（推荐v1.0.0阶段）**
- **UptimeRobot**（免费）：外部监控，5分钟轮询 `/health`
- **Sentry**（免费额度）：Python/FastAPI 错误追踪
- **Grafana Cloud Free**：最多3个仪表板，14天保留

**方案B：自托管（生产级）**
- **Prometheus + Grafana**：已有docker-compose配置
- **Loki**：日志聚合（替代EFK）
- **Alertmanager**：告警路由

**推荐路径**：v1.0阶段用方案A，验证PMF后切换方案B

### 2.2 核心监控指标

| 指标类别 | 指标名称 | 采集方式 | 告警阈值 | 严重程度 |
|---------|---------|---------|---------|---------|
| **可用性** | 服务可用率 | UptimeRobot | <99.5% | 🔴 P1 |
| **可用性** | /health 响应状态 | Prometheus | 非200 | 🔴 P1 |
| **性能** | API P50响应时间 | Prometheus histogram | >2s | 🟡 P2 |
| **性能** | API P95响应时间 | Prometheus histogram | >5s | 🟡 P2 |
| **性能** | API P99响应时间 | Prometheus histogram | >10s | 🟡 P2 |
| **错误** | HTTP 5xx 错误率 | Prometheus counter | >1% | 🔴 P1 |
| **错误** | HTTP 4xx 错误率 | Prometheus counter | >10% | 🟡 P2 |
| **错误** | 未处理异常数 | Sentry | >0 | 🔴 P1 |
| **资源** | 容器CPU使用率 | Prometheus | >80% | 🟡 P2 |
| **资源** | 容器内存使用率 | Prometheus | >85% | 🟡 P2 |
| **资源** | 磁盘使用率 | Prometheus node | >80% | 🟡 P2 |
| **限流** | Rate limit 触发次数 | 日志统计 | >100次/小时 | 🟡 P2 |
| **审计** | 审计日志写入失败 | 日志告警 | >0 | 🔴 P1 |

### 2.3 日志收集方案

**当前状态**：FastAPI 使用 Python `logging` 模块，本地 stdout 输出

**推荐改进**：
```
1. 日志格式JSON化（结构化，便于解析）
2. Docker日志驱动：json-file + logagent → Loki/Elasticsearch
3. 关键日志事件：
   - /analyze 请求/响应
   - 认证失败（暴力破解检测）
   - Rate limit 触发
   - 审计日志写入
```

**日志保留**：
- 开发环境：7天
- 生产环境：90天（`.env.example` AUDIT_RETENTION_DAYS=90 已配置）
- 压缩归档：30天后

---

## 三、GitHub API 使用追踪

### 3.1 当前GitHub集成情况

- `/api/v1/webhook`：接收 GitHub webhooks（pull_request, push, workflow_run）
- `/api/v1/review-pr`：GitHub Actions PR diff 审查
- CI workflow 使用 GitHub API 做 PR 评论

### 3.2 GitHub API Rate Limit 监控

| Token类型 | 配额 | 冷却时间 |
|----------|------|---------|
| 未认证 | 60次/小时 | 滚动窗口 |
| 已认证 (PAT) | 5,000次/小时 | 滚动窗口 |
| GitHub App | 5,000次/小时（可扩展） | 滚动窗口 |

**监控方案**：
```python
# 在 webhook handler 中添加 rate limit header 检查
def check_github_rate_limit(headers):
    remaining = int(headers.get("X-RateLimit-Remaining", 0))
    reset_time = int(headers.get("X-RateLimit-Reset", 0))
    
    if remaining < 100:
        logger.warning(f"GitHub API rate limit low: {remaining} remaining")
        # 触发告警
```

### 3.3 Token配额追踪

建议在数据库中记录每日API使用量：
```sql
CREATE TABLE github_api_usage (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    token_hash TEXT NOT NULL,  -- token前8位hash
    endpoint TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 GitHub API 降级策略

| 场景 | 降级策略 |
|------|---------|
| Rate limit <10% | 暂停非关键API调用，仅保留webhook接收 |
| Rate limit <5% | 返回缓存结果，标记"数据可能过时" |
| API 5xx 错误 | 指数退避重试（1s → 2s → 4s → 8s → 放弃） |
| 完全不可用 | 前端显示"GitHub集成暂时不可用"，不影响本地分析 |

---

## 四、健康检查机制

### 4.1 现有端点

`GET /health` → 返回 `{"status": "ok", "version": "v1.0.0"}`

### 4.2 增强型健康检查端点设计

```python
@app.get("/health/detailed")
async def health_detailed():
    """
    详细健康检查（供监控服务使用）
    返回：
    - 服务状态
    - 依赖服务状态（DB、Redis可选）
    - 关键配置
    - 最近错误摘要
    """
    checks = {
        "service": "ok",
        "database": "ok",  # test sqlite connection
        "audit_log": "ok", # test write to audit db
        "rate_limiter": "ok", # check memory/counter
    }
    
    # 可选：Redis健康检查（如果启用）
    # 可选：磁盘空间检查
    
    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    status_code = 200 if overall == "ok" else 503
    
    return JSONResponse({
        "status": overall,
        "version": "v1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "uptime_seconds": get_uptime()
    }, status_code=status_code)
```

### 4.3 告警阈值汇总

| 指标 | 警告阈值 | 严重阈值 | 告警渠道 |
|------|---------|---------|---------|
| 服务不可用 | - | 任何5xx | PagerDuty / 企业微信 |
| API错误率 | >0.5% | >1% | 企业微信 |
| P95响应时间 | >3s | >5s | 企业微信 |
| CPU使用率 | >70% | >85% | 企业微信 |
| 内存使用率 | >75% | >90% | 企业微信 |
| 磁盘使用率 | >70% | >85% | 企业微信 |
| GitHub API配额 | <20% | <10% | Slack/邮件 |
| 审计日志失败 | - | >0 | PagerDuty |
| Rate limit触发 | >50次/小时 | >200次/小时 | 邮件汇总 |

### 4.4 告警通知渠道

| 严重级别 | 渠道 | 响应时间要求 |
|---------|------|------------|
| P1（立即） | 企业微信机器人 / PagerDuty | <5分钟 |
| P2（工作日） | 邮件 + Slack | <2小时 |
| P3（常规） | 邮件汇总（每日） | 次日 |

---

## 五、测试覆盖评估（v1.0.0）

### 5.1 当前测试现状

| 测试文件 | 覆盖范围 | 说明 |
|---------|---------|------|
| `backend/tests/test_analyzers.py` | 仅分析器 | 已有静态分析器单元测试 |

**缺口分析**：
- ❌ 无 API 端点测试（TestClient）
- ❌ 无认证流程测试
- ❌ 无速率限制测试
- ❌ 无 webhook 测试
- ❌ 无数据库/SQLite操作测试
- ❌ 无集成测试
- ❌ 无性能/压力测试

### 5.2 测试覆盖率估算

```
当前覆盖率：~15-20%（仅核心分析逻辑）
建议目标：60%+（v1.1）
理想目标：80%+（v1.2+）
```

### 5.3 建议补充测试用例

**优先级 P1（必须补）**
```python
# 1. API端点测试
test_health_endpoint.py
test_analyze_endpoint_success.py
test_analyze_endpoint_validation_errors.py
test_analyze_endpoint_rate_limit.py

# 2. 认证测试
test_register_success.py
test_register_duplicate_email.py
test_login_success.py
test_login_wrong_password.py
test_auth_token_expiry.py

# 3. 安全测试
test_sqlite_injection.py
test_code_input_sanitization.py
test_webhook_signature_verification.py
```

**优先级 P2（应该补）**
```python
# 4. 分析器深度测试
test_logic_analyzer_edge_cases.py
test_security_analyzer_xss.py
test_debt_analyzer_duplication.py

# 5. 团队功能测试
test_create_team.py
test_invite_member.py
test_remove_member_unauthorized.py

# 6. 报告生成测试
test_html_report_generation.py
test_text_report_generation.py
```

**优先级 P3（建议补）**
```python
# 7. 压力测试
test_concurrent_requests.py
test_rate_limiter_under_load.py

# 8. 回归测试套件
pytest --forked（并发测试）
```

### 5.4 回归测试机制

**方案：GitHub Actions + pytest**

```yaml
# .github/workflows/test.yml（建议新增）
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --tb=short
      - name: Upload coverage
        if: always()
        uses: codecov/codecov-action@v4
```

**每次PR必须通过**：单元测试 + lint + type check

**回归测试执行频率**：
- 每次PR：完整测试套件
- 每次main合并：覆盖率对比（下降>5%阻止合并）
- 每日：完整测试 + 慢查询分析

---

## 六、实施路线图

### Phase 1：立即可做（1-2天）
- [ ] 启用 UptimeRobot 监控 `/health`
- [ ] 配置 Sentry SDK（5分钟集成）
- [ ] 增强 `/health` → `/health/detailed`
- [ ] 添加日志JSON化

### Phase 2：第一周
- [ ] 添加 API 端点测试（pytest + TestClient）
- [ ] 添加认证流程测试
- [ ] 配置 Prometheus（已有docker-compose，启用即可）
- [ ] 配置 Grafana Dashboard

### Phase 3：第一个月
- [ ] GitHub API rate limit 监控
- [ ] 压力测试 + 性能基线
- [ ] 自动化告警配置（Alertmanager）
- [ ] 测试覆盖率提升至 60%+

---

## 七、快速启动配置（Docker Compose + Prometheus）

### prometheus.yml（在项目根目录创建）

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'codelens-backend'
    static_configs:
      - targets: ['backend:8090']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### docker-compose.override.yml（生产追加）

```yaml
services:
  backend:
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9091:9090"  # 暴露metrics
  
  prometheus:
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
```

---

## 八、关键联系人

| 角色 | 职责 | 备注 |
|------|------|------|
| 真理（测试专家） | 监控机制实施、测试覆盖 | 本文档负责人 |
| 鸣商（营销专家） | 进度汇报、需求反馈 | 汇报对象 |

---

*文档版本：1.0 | 制定日期：2026-04-21 | 负责人：真理*
