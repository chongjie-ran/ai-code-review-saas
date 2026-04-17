"""
CodeLens AI - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class AnalyzeOptions(BaseModel):
    check_security: bool = True
    check_logic: bool = True
    check_debt: bool = True


class AnalyzeRequest(BaseModel):
    code: str = Field(..., description="代码片段")
    language: Literal["python", "javascript", "typescript", "java", "go", "rust"] = Field(
        ..., description="语言类型"
    )
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)


class Issue(BaseModel):
    type: Literal["logic", "security", "debt"] = Field(..., description="问题类型")
    severity: Literal["high", "medium", "low"] = Field(..., description="严重级别")
    line: int = Field(..., description="问题所在行")
    column: Optional[int] = Field(None, description="问题所在列")
    message: str = Field(..., description="问题描述")
    rule_id: str = Field(..., description="规则ID")
    fix: Optional[str] = Field(None, description="修复建议")


class IssueSummary(BaseModel):
    total: int
    high: int
    medium: int
    low: int


class AnalyzeResponse(BaseModel):
    issues: list[Issue]
    summary: IssueSummary
    score: int = Field(..., ge=0, le=100, description="代码质量分数")
    language: str
    lines_of_code: int


class HealthResponse(BaseModel):
    status: str
    service: str = "CodeLens AI"
    version: str = "v0.4.0"


# ─── Auth Schemas ────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")
    name: Optional[str] = Field(None, description="显示名称")


class UserLogin(BaseModel):
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Team Schemas ────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="团队名称")


class TeamInvite(BaseModel):
    email: str = Field(..., description="被邀请用户邮箱")
    role: Literal["admin", "member"] = Field(default="member", description="角色")


class TeamMemberResponse(BaseModel):
    user_id: int
    email: str
    name: Optional[str]
    role: str
    invited_at: str


class TeamResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: str
    members: list[TeamMemberResponse] = []
