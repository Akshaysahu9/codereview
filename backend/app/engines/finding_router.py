"""Route linter/heuristic findings to issues vs best_practices vs optimizations."""

from app.schemas import Issue, IssueCategory, OptimizationSuggestion, Severity

IMPORTANT_CATEGORIES = {
    IssueCategory.SYNTAX,
    IssueCategory.LOGIC,
    IssueCategory.INFINITE_LOOP,
    IssueCategory.NULL_POINTER,
    IssueCategory.SECURITY,
    IssueCategory.RUNTIME,
    IssueCategory.COMPLEXITY,
}


def linter_failure_issue(tool: str, message: str) -> Issue:
    return Issue(
        category=IssueCategory.RUNTIME,
        severity=Severity.WARNING,
        title=f"{tool} unavailable",
        message=message,
        suggestion=f"Install {tool} so real lint errors are detected. See backend/scripts/install-engines.bat",
        confidence=0.99,
    )


def route_linter_finding(
    finding: Issue,
) -> tuple[str, Issue | OptimizationSuggestion]:
    """Return ('issues' | 'best_practices' | 'optimizations', item)."""
    if finding.category == IssueCategory.OPTIMIZATION:
        return (
            "optimizations",
            OptimizationSuggestion(
                title=finding.title,
                description=finding.message,
                impact="high" if finding.severity == Severity.ERROR else "medium",
                line=finding.line,
                before=finding.code_snippet,
            ),
        )

    if finding.severity == Severity.ERROR:
        return "issues", finding

    if finding.category in IMPORTANT_CATEGORIES:
        return "issues", finding

    msg = finding.message.lower()
    if finding.severity == Severity.WARNING and any(
        k in msg for k in ("assign", "infinite", "undefined", "null", "syntax", "unsafe", "eval")
    ):
        return "issues", finding

    return "best_practices", finding
