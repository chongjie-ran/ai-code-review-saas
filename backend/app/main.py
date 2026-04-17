"""
CodeLens AI - FastAPI Backend
AI代码审查SaaS后端服务
"""
import logging
import os
from datetime import datetime
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, Request, Response, Depends, Body, Security, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # noqa: F401 - imported for backwards compat
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    IssueSummary,
    HealthResponse,
    UserRegister,
    UserLogin,
    TokenResponse,
    TeamCreate,
    TeamInvite,
    TeamResponse,
)

# Enterprise imports
from . import audit, sso, compliance, rate_limiter, encryption
from .analyzers.static_analyzer import LogicAnalyzer
from .analyzers.security_analyzer import SecurityAnalyzer
from .analyzers.debt_analyzer import DebtAnalyzer
from .rules.rule_engine import rule_engine
from .storage import session_store
from .report import generate_html_report, generate_text_summary
from .webhook import webhook_handler
from . import auth

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

# Security scheme (now using auth.security internally)


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
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(rate_limiter.RateLimitMiddleware)

# Audit middleware (auto-logs all API requests)
app.add_middleware(audit.AuditMiddleware)


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
    logger.info("CodeLens AI Backend v0.4.0 starting...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("CodeLens AI Backend shutting down...")


# ─── Auth Dependencies ────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(auth.security),
) -> dict:
    """Get current authenticated user"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await auth.get_current_user(credentials)


# ─── Core Endpoints ───────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(status="ok", version="v1.0.0")


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(
    req: AnalyzeRequest = Body(...),
    user: Optional[dict] = Security(auth.get_optional_user),
):
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

    logger.info(f"Analyze request: lang={req.language}, len={len(req.code)}, user={user}")

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


# ─── Auth Endpoints ───────────────────────────────────────────

@app.post("/api/v1/auth/register", response_model=TokenResponse, tags=["认证"])
async def register(req: UserRegister):
    """
    Register a new user account.
    
    Returns JWT token for immediate authentication.
    """
    user = auth.register_user(req.email, req.password, req.name)
    token_data = auth.login_user(req.email, req.password)
    return TokenResponse(**token_data)


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["认证"])
async def login(req: UserLogin):
    """
    Authenticate user and return JWT token.
    
    Token expires in 7 days.
    """
    return auth.login_user(req.email, req.password)


@app.get("/api/v1/auth/me", tags=["认证"])
async def get_me(user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    
    Requires authentication.
    """
    return user


# ─── Team Endpoints ───────────────────────────────────────────

@app.post("/api/v1/teams", response_model=TeamResponse, tags=["团队"])
async def create_team(
    req: TeamCreate,
    user: dict = Depends(get_current_user),
):
    """
    Create a new team.
    
    The creating user becomes the team owner.
    Requires authentication.
    """
    team = auth.create_team(req.name, user["id"])
    # Get full team with members
    return auth.get_team(team["id"], user["id"])


@app.get("/api/v1/teams", tags=["团队"])
async def list_teams(user: dict = Depends(get_current_user)):
    """
    List all teams the current user belongs to.
    
    Requires authentication.
    """
    teams = auth.get_user_teams(user["id"])
    return {"teams": teams, "count": len(teams)}


@app.get("/api/v1/teams/{team_id}", response_model=TeamResponse, tags=["团队"])
async def get_team(
    team_id: int,
    user: dict = Depends(get_current_user),
):
    """
    Get team details.
    
    Only team members can view team details.
    Requires authentication.
    """
    return auth.get_team(team_id, user["id"])


@app.post("/api/v1/teams/{team_id}/invite", tags=["团队"])
async def invite_member(
    team_id: int,
    req: TeamInvite,
    user: dict = Depends(get_current_user),
):
    """
    Invite a user to join the team.
    
    Only owner or admin can invite members.
    Requires authentication.
    """
    result = auth.invite_to_team(team_id, user["id"], req.email, req.role)
    return {"message": "Invitation sent", **result}


@app.delete("/api/v1/teams/{team_id}/members/{user_id}", tags=["团队"])
async def remove_member(
    team_id: int,
    user_id: int,
    user: dict = Depends(get_current_user),
):
    """
    Remove a member from the team.
    
    Only owner or admin can remove members.
    Cannot remove the team owner.
    Requires authentication.
    """
    success = auth.remove_from_team(team_id, user["id"], user_id)
    return {"deleted": success, "user_id": user_id}


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


# ─── OpenAPI Tags ─────────────────────────────────────────────

app.openapi_tags = [
    {"name": "认证", "description": "用户注册、登录、Token管理"},
    {"name": "团队", "description": "团队创建、成员管理、权限控制"},
    {"name": "分析", "description": "代码分析相关端点"},
    {"name": "报告", "description": "报告生成和获取"},
    {"name": "Webhook", "description": "CI/CD集成"},
]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)


# ─── SSO / Enterprise Auth Endpoints ───────────────────────────────────────

@app.get("/api/v1/auth/sso/providers", tags=["SSO"])
async def list_sso_providers():
    """
    List all configured SSO providers (SAML and OIDC).
    Returns provider IDs for initiating SSO login.
    """
    providers = sso.sso_registry.list_providers()
    return {"providers": providers, "count": len(providers)}


@app.get("/api/v1/auth/saml/login", tags=["SSO"])
async def saml_login(
    provider_id: str = Query(..., description="SAML provider ID from /providers list"),
    redirect_uri: str = Query(..., description="URL to redirect after SAML callback"),
):
    """
    Initiate SAML SSO login flow.
    Returns redirect URL to the configured SAML Identity Provider.
    """
    result = sso.sso_registry.get_saml_login_url(provider_id, redirect_uri)
    return {
        "type": "saml",
        "redirect_url": result["redirect_url"],
        "request_id": result["request_id"],
        "provider_label": result["provider_label"],
    }


@app.post("/api/v1/auth/saml/callback", response_model=TokenResponse, tags=["SSO"])
async def saml_callback(
    SAMLResponse: str = Body(..., embed=True),
    RelayState: Optional[str] = Body(None, embed=True),
):
    """
    Handle SAML Response from Identity Provider.
    Automatically provisions or retrieves user and returns JWT token.
    """
    if not SAMLResponse:
        raise APIError(400, "Missing SAMLResponse")

    user_info = sso.sso_registry.handle_saml_response(SAMLResponse, RelayState or "")
    result = sso.provision_sso_user(
        provider="saml",
        email=user_info["email"],
        name=user_info.get("name"),
        external_id=user_info.get("external_id"),
    )
    return TokenResponse(**result)


@app.get("/api/v1/auth/oidc/login", tags=["SSO"])
async def oidc_login(
    provider_id: str = Query(..., description="OIDC provider ID from /providers list"),
    redirect_uri: str = Query(..., description="OAuth redirect URI"),
):
    """
    Initiate OIDC authorization code flow.
    Returns redirect URL to the configured OIDC provider.
    """
    result = sso.sso_registry.get_oidc_login_url(provider_id, redirect_uri)
    return {
        "type": "oidc",
        "redirect_url": result["redirect_url"],
        "state": result["state"],
        "provider_label": result["provider_label"],
    }


@app.post("/api/v1/auth/oidc/callback", response_model=TokenResponse, tags=["SSO"])
async def oidc_callback(
    code: str = Body(..., embed=True),
    state: str = Body(..., embed=True),
    redirect_uri: str = Body(..., embed=True),
    provider_id: str = Body(..., embed=True),
):
    """
    Exchange OIDC authorization code for tokens.
    Automatically provisions or retrieves user and returns JWT token.
    """
    user_info = await sso.sso_registry.exchange_oidc_code(provider_id, code, state, redirect_uri)
    result = sso.provision_sso_user(
        provider="oidc",
        email=user_info["email"],
        name=user_info.get("name"),
        external_id=user_info.get("sub"),
    )
    return TokenResponse(**result)


# ─── Audit Log Endpoints ────────────────────────────────────────────────

@app.get("/api/v1/audit/logs", tags=["审计"])
async def get_audit_logs(
    user: dict = Depends(get_current_user),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource: Optional[str] = Query(None, description="Filter by resource type"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    start_date: Optional[str] = Query(None, description="ISO date start"),
    end_date: Optional[str] = Query(None, description="ISO date end"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Query audit logs with filters.
    Only accessible by authenticated users. Team admins can view team-scoped logs.
    Requires authentication.
    """
    if team_id:
        try:
            auth.get_team(team_id, user["id"])
        except HTTPException:
            raise APIError(403, "Not authorized to view this team's audit logs")

    result = audit.query_audit_logs(
        user_id=user["id"],
        team_id=team_id,
        action=action,
        resource=resource,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return result


@app.get("/api/v1/audit/logs/export", tags=["审计"])
async def export_audit_logs(
    user: dict = Depends(get_current_user),
    format: Literal["json", "csv"] = Query("json", description="Export format"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Export audit logs as JSON or CSV.
    Requires authentication.
    """
    content = audit.export_audit_logs(
        start_date=start_date,
        end_date=end_date,
        format=format,
    )
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"
    media_type = "application/json" if format == "json" else "text/csv"
    return Response(
        content=content,
        media_type=f"{media_type}; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─── Compliance Report Endpoints ──────────────────────────────────────────

@app.get("/api/v1/compliance/soc2", tags=["合规"])
async def get_soc2_report(
    user: dict = Depends(get_current_user),
    team_id: Optional[int] = Query(None),
):
    """Generate SOC2 Type II compliance report. Requires authentication."""
    team_name = "CodeLens AI Team"
    if team_id:
        try:
            team = auth.get_team(team_id, user["id"])
            team_name = team["name"]
        except HTTPException:
            raise APIError(403, "Not authorized")
    report = compliance.generate_soc2_report(None, team_name)
    return report


@app.get("/api/v1/compliance/soc2/html", tags=["合规"])
async def get_soc2_report_html(
    user: dict = Depends(get_current_user),
    team_id: Optional[int] = Query(None),
):
    """Generate SOC2 compliance report as HTML. Requires authentication."""
    team_name = "CodeLens AI Team"
    if team_id:
        try:
            team = auth.get_team(team_id, user["id"])
            team_name = team["name"]
        except HTTPException:
            raise APIError(403, "Not authorized")
    report = compliance.generate_soc2_report(None, team_name)
    html = compliance.generate_compliance_html_report(report, "soc2")
    return HTMLResponse(content=html)


@app.get("/api/v1/compliance/iso27001", tags=["合规"])
async def get_iso27001_report(
    user: dict = Depends(get_current_user),
    team_id: Optional[int] = Query(None),
):
    """Generate ISO 27001:2022 compliance report. Requires authentication."""
    team_name = "CodeLens AI Team"
    if team_id:
        try:
            team = auth.get_team(team_id, user["id"])
            team_name = team["name"]
        except HTTPException:
            raise APIError(403, "Not authorized")
    report = compliance.generate_iso27001_report(None, team_name)
    return report


@app.get("/api/v1/compliance/iso27001/html", tags=["合规"])
async def get_iso27001_report_html(
    user: dict = Depends(get_current_user),
    team_id: Optional[int] = Query(None),
):
    """Generate ISO 27001 compliance report as HTML. Requires authentication."""
    team_name = "CodeLens AI Team"
    if team_id:
        try:
            team = auth.get_team(team_id, user["id"])
            team_name = team["name"]
        except HTTPException:
            raise APIError(403, "Not authorized")
    report = compliance.generate_iso27001_report(None, team_name)
    html = compliance.generate_compliance_html_report(report, "iso27001")
    return HTMLResponse(content=html)


@app.get("/api/v1/compliance/hipaa", tags=["合规"])
async def get_hipaa_report(
    user: dict = Depends(get_current_user),
    team_id: Optional[int] = Query(None),
):
    """Generate HIPAA Security Rule compliance report. Requires authentication."""
    team_name = "CodeLens AI Team"
    if team_id:
        try:
            team = auth.get_team(team_id, user["id"])
            team_name = team["name"]
        except HTTPException:
            raise APIError(403, "Not authorized")
    report = compliance.generate_hipaa_report(None, team_name)
    return report


@app.get("/api/v1/compliance/hipaa/html", tags=["合规"])
async def get_hipaa_report_html(
    user: dict = Depends(get_current_user),
    team_id: Optional[int] = Query(None),
):
    """Generate HIPAA compliance report as HTML. Requires authentication."""
    team_name = "CodeLens AI Team"
    if team_id:
        try:
            team = auth.get_team(team_id, user["id"])
            team_name = team["name"]
        except HTTPException:
            raise APIError(403, "Not authorized")
    report = compliance.generate_hipaa_report(None, team_name)
    html = compliance.generate_compliance_html_report(report, "hipaa")
    return HTMLResponse(content=html)


# ─── Encryption Utilities ────────────────────────────────────────────────

@app.post("/api/v1/enterprise/encrypt", tags=["企业"])
async def encrypt_data(
    plaintext: str = Body(..., description="Data to encrypt"),
    user: dict = Depends(get_current_user),
):
    """
    Encrypt sensitive data using AES-256-GCM.
    Enterprise feature for protecting secrets at rest.
    Requires authentication.
    """
    encrypted = encryption.encrypt(plaintext)
    return {"encrypted": encrypted, "algorithm": "AES-256-GCM"}


@app.post("/api/v1/enterprise/decrypt", tags=["企业"])
async def decrypt_data(
    encrypted: str = Body(..., description="Encrypted data"),
    user: dict = Depends(get_current_user),
):
    """Decrypt AES-256-GCM encrypted data. Requires authentication."""
    try:
        plaintext = encryption.decrypt(encrypted)
        return {"plaintext": plaintext}
    except ValueError as e:
        raise APIError(400, "Decryption failed", str(e))


@app.get("/api/v1/enterprise/status", tags=["企业"])
async def enterprise_status(user: dict = Depends(get_current_user)):
    """
    Get enterprise feature status for the current deployment.
    Shows which enterprise features are enabled.
    Requires authentication.
    """
    saml_configs, oidc_configs = sso.load_idp_configs()
    return {
        "version": "v1.0.0",
        "enterprise": True,
        "features": {
            "sso": {
                "enabled": len(saml_configs) + len(oidc_configs) > 0,
                "saml_providers": len(saml_configs),
                "oidc_providers": len(oidc_configs),
            },
            "audit_logs": {"enabled": True, "retention_days": audit.AUDIT_RETENTION_DAYS},
            "compliance": {"soc2": True, "iso27001": True, "hipaa": True},
            "rate_limiting": {
                "enabled": True,
                "default_limit": rate_limiter.DEFAULT_LIMIT,
                "default_window": rate_limiter.DEFAULT_WINDOW,
            },
            "encryption": {"algorithm": "AES-256-GCM", "enabled": True},
            "docker_compose": {"available": True},
        },
    }


# ─── OpenAPI Tags Update ──────────────────────────────────────────────────

app.openapi_tags = [
    {"name": "认证", "description": "用户注册、登录、Token管理"},
    {"name": "SSO", "description": "企业SSO登录 (SAML 2.0 / OIDC)"},
    {"name": "团队", "description": "团队创建、成员管理、权限控制"},
    {"name": "审计", "description": "审计日志查询和导出"},
    {"name": "合规", "description": "SOC2 / ISO27001 / HIPAA 合规报告"},
    {"name": "企业", "description": "企业级功能 (加密、状态)"},
    {"name": "分析", "description": "代码分析相关端点"},
    {"name": "报告", "description": "报告生成和获取"},
    {"name": "Webhook", "description": "CI/CD集成"},
]
