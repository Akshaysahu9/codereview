from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


class IssueCategory(str, Enum):
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    NULL_POINTER = "null_pointer"
    INFINITE_LOOP = "infinite_loop"
    COMPLEXITY = "complexity"
    OPTIMIZATION = "optimization"
    BEST_PRACTICE = "best_practice"
    DUPLICATE = "duplicate"
    UNUSED = "unused"
    NAMING = "naming"
    SECURITY = "security"


class Issue(BaseModel):
    category: IssueCategory
    severity: Severity
    title: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ComplexityMetric(BaseModel):
    cyclomatic_complexity: int
    lines_of_code: int
    function_count: int
    max_function_lines: int
    max_nesting_depth: int
    rating: str
    details: list[str] = Field(default_factory=list)


class OptimizationSuggestion(BaseModel):
    title: str
    description: str
    impact: str
    line: Optional[int] = None
    before: Optional[str] = None
    after: Optional[str] = None


class ReviewRequest(BaseModel):
    code: str
    language: Language
    title: Optional[str] = None


class ReviewResponse(BaseModel):
    language: Language
    score: int
    summary: str
    issues: list[Issue]
    complexity: ComplexityMetric
    optimizations: list[OptimizationSuggestion]
    best_practices: list[Issue]
    passed_checks: list[str] = Field(default_factory=list)
    analysis_engine: str = "static"
    lint_engine: str = ""
    critical_findings: list[str] = Field(default_factory=list)
    issue_stats: dict[str, int] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    code: str
    language: Language
    focus: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    key_concepts: list[str] = Field(default_factory=list)
    line_by_line: list[dict[str, Any]] = Field(default_factory=list)


class GenerateTestsRequest(BaseModel):
    code: str
    language: Language
    framework: Optional[str] = None


class GenerateTestsResponse(BaseModel):
    framework: str
    tests: str
    test_count: int
    coverage_notes: list[str] = Field(default_factory=list)


class FixCodeRequest(BaseModel):
    code: str
    language: Language
    issues: Optional[list[Issue]] = None


class FixCodeResponse(BaseModel):
    fixed_code: str
    changes_summary: list[str]
    issues_addressed: int


class HistoryCreate(BaseModel):
    language: Language
    code_snippet: str
    title: Optional[str] = None
    review_type: str = "review"
    result_json: str
    score: Optional[int] = None


class HistoryItem(BaseModel):
    id: int
    language: str
    code_snippet: str
    title: Optional[str]
    review_type: str
    result_json: str
    score: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int


class HistoryStatsResponse(BaseModel):
    total_analyses: int
    total_reviews: int
    average_score: Optional[float] = None
    by_language: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
