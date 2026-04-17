"""
CodeLens AI - FastAPI Backend
AI代码审查SaaS后端服务
"""
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    IssueSummary,
    HealthResponse,
)
from .analyzers.static_analyzer import LogicAnalyzer
from .analyzers.security_analyzer import SecurityAnalyzer
from .analyzers.debt_analyzer import DebtAnalyzer
from .rules.rule_engine import rule_engine
from .storage import session_store
from .report import generate_html_report, generate_text_summary
from .webhook import webhook_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Webhook secret from environment
WEBHOOK_SECRET = os.getenv("CODELENS_WEBHOOK_SECRET")

# Analysis engines
logic_analyzer = LogicAnalyzer(rule_engine)
security_analyzer = SecurityAnalyzer(rule_engine)
debt_analyzer = DebtAnalyzer(rule_engine)


# ───────────────────────────────────────────────────────────────
# Exception Handlers
# ───────────────────────────────────────────────────────────────

class APIError(Exception):
    """Standard API error"""

    def __init__(self, status_code: int, message: str, detail: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail or message


def build_error_response(status_code: int, message: str, detail: Optional[str] = None) -> dict:
    """Build standardized error response"""
    return {
        "error": {
            "code": status_code,
            "message": message,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }


# ───────────────────────────────────────────────────────────────
# FastAPI App
# ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="CodeLens AI",
    description="AI代码审查SaaS - 专注AI生成代码的质量保障",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception handlers ───────────────────────────────────────

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(exc.status_code, exc.message, exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_response(
            HTTP_422_UNPROCESSABLE_ENTITY,
            "请求参数验证失败",
            str(exc.errors()),
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(exc.status_code, exc.detail or "HTTP error"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=build_error_response(500, "服务器内部错误", str(exc)),
    )


# ─── Lifespan ─────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("CodeLens AI Backend v0.3.0 starting...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("CodeLens AI Backend shutting down...")


# ─── Core Endpoints ───────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(status="ok")


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    Analyze code snippet

    Detects in AI-generated code:
    - Logic errors (logic)
    - Security vulnerabilities (security)
    - Technical debt (debt)

    Returns session_id in X-Session-ID header for report retrieval.
    """
    # Input validation
    if not req.code or not req.code.strip():
        raise APIError(400, "代码不能为空", "code field must be non-empty")

    if len(req.code) > 100_000:
        raise APIError(400, "代码超过100KB限制", f"code length: {len(req.code)}")

    logger.info(f"Analyze request: lang={req.language}, len={len(req.code)}")

    issues = []

    # Logic error detection
    if req.options.check_logic:
        issues.extend(logic_analyzer.analyze(req.code, req.language))

    # Security vulnerability detection
    if req.options.check_security:
        issues.extend(security_analyzer.analyze(req.code, req.language))

    # Technical debt detection
    if req.options.check_debt:
        issues.extend(debt_analyzer.analyze(req.code, req.language))

    # Compute summary
    summary = IssueSummary(
        total=len(issues),
        high=sum(1 for i in issues if i.severity == "high"),
        medium=sum(1 for i in issues if i.severity == "medium"),
        low=sum(1 for i in issues if i.severity == "low"),
    )

    # Quality score: 100 - high*10 - med*3 - low*1, minimum 0
    score = max(0, 100 - summary.high * 10 - summary.medium * 3 - summary.low * 1)

    # Deduplicate issues (same rule_id + line)
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue.rule_id, issue.line)
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    response = AnalyzeResponse(
        issues=unique_issues,
        summary=summary,
        score=score,
        language=req.language,
        lines_of_code=len(req.code.split("\n")),
    )

    # Store session
    session_id = session_store.store(response)

    logger.info(
        f"Analysis complete: score={score}, "
        f"issues={summary.total} (H:{summary.high}/M:{summary.medium}/L:{summary.low}), "
        f"session={session_id}"
    )

    return response


# ─── Report Endpoints ─────────────────────────────────────────

@app.get("/api/v1/report/{session_id}")
async def get_report(session_id: str, fmt: Optional[str] = "html"):
    """
    Retrieve analysis report by session_id.

    Args:
        session_id: Session ID returned from /analyze
        fmt: Output format - 'html' (default) or 'text'
    """
    if len(session_id) > 64 or not session_id.replace("-", "").replace("_", "").isalnum():
        raise APIError(400, "无效的 session_id")

    response = session_store.get(session_id)
    if response is None:
        raise APIError(404, f"Session '{session_id}' 不存在或已过期", "session not found")

    if fmt == "text":
        content = generate_text_summary(response, session_id)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
        )

    # Default: HTML
    html = generate_html_report(response, session_id)
    return HTMLResponse(content=html)


@app.get("/api/v1/sessions")
async def list_sessions(limit: int = 50):
    """List recent analysis sessions"""
    if limit < 1 or limit > 200:
        raise APIError(400, "limit 必须在 1-200 之间")
    sessions = session_store.list_sessions(limit=limit)
    return {"sessions": sessions, "count": len(sessions)}


@app.delete("/api/v1/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if not session_store.delete(session_id):
        raise APIError(404, f"Session '{session_id}' 不存在")
    return {"deleted": session_id}


# ─── Webhook Endpoint ─────────────────────────────────────────

@app.post("/api/v1/webhook")
async def webhook(request: Request, x_hub_signature_256: Optional[str] = None):
    """
    Webhook endpoint for external CI/CD system integration.

    Supports:
    - GitHub webhooks (pull_request, push, workflow_run)
    - Generic JSON payloads

    Set CODELENS_WEBHOOK_SECRET env var to enable HMAC signature verification.
    """
    body = await request.body()

    # Verify signature
    if x_hub_signature_256:
        if not webhook_handler.verify_signature(body, x_hub_signature_256):
            logger.warning("Webhook signature verification failed")
            raise APIError(401, "Webhook signature verification failed")

    # Parse event type
    event_type = request.headers.get("x-github-event", "unknown")
    content_type = request.headers.get("content-type", "")

    logger.info(f"Webhook received: event={event_type}, size={len(body)} bytes")

    try:
        import json
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError as e:
        raise APIError(400, "Invalid JSON payload", str(e))

    # Parse event
    parsed = webhook_handler.parse_github_event(event_type, payload)

    # Log event
    logger.info(f"Webhook event processed: {parsed.get('type')} - {event_type}")

    return {
        "received": True,
        "event": event_type,
        "parsed": parsed,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── GitHub Actions PR Review Helper ──────────────────────────

@app.post("/api/v1/review-pr")
async def review_pr(request: Request):
    """
    Convenience endpoint for GitHub Actions to submit PR diff for review.

    Accepts JSON with 'files' (list of {path, content, language}) and returns
    aggregated analysis across all files.
    """
    try:
        body = await request.json()
    except Exception:
        raise APIError(400, "Invalid JSON body")

    files = body.get("files", [])
    if not files:
        raise APIError(400, "No files provided")

    if len(files) > 100:
        raise APIError(400, "Too many files (max 100)")

    all_issues = []
    total_loc = 0

    for f in files:
        code = f.get("content", "")
        lang = f.get("language", "python")
        path = f.get("path", "unknown")

        if not code or not code.strip():
            continue

        if len(code) > 100_000:
            code = code[:100_000]

        # Run all analyzers
        issues = []
        issues.extend(logic_analyzer.analyze(code, lang))
        issues.extend(security_analyzer.analyze(code, lang))
        issues.extend(debt_analyzer.analyze(code, lang))

        # Add file path context
        for issue in issues:
            issue.rule_id = f"{path}:{issue.rule_id}"

        all_issues.extend(issues)
        total_loc += len(code.split("\n"))

    # Deduplicate
    seen = set()
    unique_issues = []
    for issue in all_issues:
        key = (issue.rule_id, issue.line)
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    summary = IssueSummary(
        total=len(unique_issues),
        high=sum(1 for i in unique_issues if i.severity == "high"),
        medium=sum(1 for i in unique_issues if i.severity == "medium"),
        low=sum(1 for i in unique_issues if i.severity == "low"),
    )
    score = max(0, 100 - summary.high * 10 - summary.medium * 3 - summary.low * 1)

    response = AnalyzeResponse(
        issues=unique_issues,
        summary=summary,
        score=score,
        language="multi",
        lines_of_code=total_loc,
    )

    session_id = session_store.store(response)

    return {
        "session_id": session_id,
        "report_url": f"/api/v1/report/{session_id}",
        **response.model_dump(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
