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
    language: Literal["python", "javascript", "typescript", "java", "go"] = Field(
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
    version: str = "v0.1.0"
