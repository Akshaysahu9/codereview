"""Explain, fix, and test helpers (offline)."""

from typing import Optional

from app.analyzers.smart_explain import explain_code as smart_explain
from app.analyzers.smart_fix import apply_smart_fix
from app.analyzers.test_generator import generate_tests as offline_tests
from app.schemas import (
    ExplainResponse,
    FixCodeResponse,
    GenerateTestsResponse,
    Issue,
    IssueCategory,
    Language,
    Severity,
)


class ToolService:
    async def explain_code(
        self, code: str, language: Language, focus: Optional[str] = None
    ) -> ExplainResponse:
        result = smart_explain(code, language)
        if focus:
            result = result.model_copy(
                update={"explanation": f"[Focus: {focus}] {result.explanation}"}
            )
        return result

    async def generate_tests(
        self, code: str, language: Language, framework: Optional[str] = None
    ) -> GenerateTestsResponse:
        return offline_tests(code, language, framework)

    async def fix_code(
        self, code: str, language: Language, issues: Optional[list[Issue]] = None
    ) -> FixCodeResponse:
        critical = [
            i
            for i in (issues or [])
            if i.severity in (Severity.ERROR, Severity.WARNING)
            and i.category not in (IssueCategory.NAMING, IssueCategory.DUPLICATE)
        ][:25]
        result = apply_smart_fix(code, language, critical or (issues or []))
        return FixCodeResponse(
            fixed_code=result.fixed_code,
            changes_summary=result.changes_summary,
            issues_addressed=result.issues_addressed,
        )


tool_service = ToolService()
