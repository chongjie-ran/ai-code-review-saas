"""
CodeLens AI - FastAPI Backend
AI代码审查SaaS后端服务
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    IssueSummary,
    HealthResponse,
)
from app.analyzers.static_analyzer import LogicAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer
from app.analyzers.debt_analyzer import DebtAnalyzer
from app.rules.rule_engine import rule_engine

# 分析器实例
logic_analyzer = LogicAnalyzer(rule_engine)
security_analyzer = SecurityAnalyzer(rule_engine)
debt_analyzer = DebtAnalyzer(rule_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动和关闭事件"""
    print("CodeLens AI Backend starting...")
    yield
    print("CodeLens AI Backend shutting down...")


app = FastAPI(
    title="CodeLens AI",
    description="AI代码审查SaaS - 专注AI生成代码的质量保障",
    version="v0.1.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    return HealthResponse(status="ok")


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    分析代码片段

    检测AI生成代码的:
    - 逻辑错误 (logic)
    - 安全漏洞 (security)
    - 技术债务 (debt)
    """
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="代码不能为空")

    if len(req.code) > 100_000:
        raise HTTPException(status_code=400, detail="代码超过100KB限制")

    issues = []

    # 逻辑错误检测
    if req.options.check_logic:
        issues.extend(logic_analyzer.analyze(req.code, req.language))

    # 安全漏洞检测
    if req.options.check_security:
        issues.extend(security_analyzer.analyze(req.code, req.language))

    # 技术债务检测
    if req.options.check_debt:
        issues.extend(debt_analyzer.analyze(req.code, req.language))

    # 计算摘要
    summary = IssueSummary(
        total=len(issues),
        high=sum(1 for i in issues if i.severity == "high"),
        medium=sum(1 for i in issues if i.severity == "medium"),
        low=sum(1 for i in issues if i.severity == "low"),
    )

    # 计算质量分数 (100 - 高*10 - 中*3 - 低*1, 最低0)
    score = max(
        0,
        100
        - summary.high * 10
        - summary.medium * 3
        - summary.low * 1,
    )

    # 去掉重复问题(同规则同行的)
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue.rule_id, issue.line)
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    return AnalyzeResponse(
        issues=unique_issues,
        summary=summary,
        score=score,
        language=req.language,
        lines_of_code=len(req.code.split("\n")),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
