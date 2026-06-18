"""Post-process analyzer output: dedupe, rank, filter noise, build executive summary."""

from app.schemas import Issue, ReviewResponse, Severity

SEVERITY_ORDER = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.SUGGESTION: 2,
    Severity.INFO: 3,
}

# Never show these noisy/low-value rules to users
BLOCKED_TITLES = {
    "short variable name",
    "non-descriptive variable",
    "poor function name",
}


def _issue_key(issue: Issue) -> str:
    return f"{issue.category}:{issue.line}:{issue.title}:{issue.message[:60]}"


def dedupe_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[str] = set()
    result: list[Issue] = []
    for issue in issues:
        key = _issue_key(issue)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def sort_issues(issues: list[Issue]) -> list[Issue]:
    return sorted(
        issues,
        key=lambda i: (SEVERITY_ORDER.get(i.severity, 9), i.line or 9999, i.title),
    )


def filter_noise(issues: list[Issue]) -> list[Issue]:
    """Remove low-confidence heuristics and blocked noise."""
    result: list[Issue] = []
    for i in issues:
        if i.title.lower() in BLOCKED_TITLES:
            continue
        if i.confidence is not None and i.confidence < 0.7:
            continue
        # Logic bugs must have a line number
        if i.category.value in ("logic", "infinite_loop", "null_pointer") and not i.line:
            continue
        result.append(i)
    return result


def count_by_severity(issues: list[Issue]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0, "info": 0, "suggestion": 0}
    for i in issues:
        counts[i.severity.value] = counts.get(i.severity.value, 0) + 1
    return counts


def build_executive_summary(
    score: int, issues: list[Issue], complexity_rating: str, best_practices: list[Issue] | None = None
) -> str:
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]
    bp_warnings = [i for i in (best_practices or []) if i.severity == Severity.WARNING]

    if not errors and not warnings:
        if bp_warnings:
            return (
                f"No critical bugs in Issues tab — {len(bp_warnings)} style warning(s) under Best Practices. "
                f"Score: {score}/100."
            )
        if infos:
            return (
                f"No bugs found — only {len(infos)} optional note(s). "
                f"Score {score}/100 reflects clean logic. Complexity: {complexity_rating}."
            )
        return f"Clean code — no bugs found. Score {score}/100. Complexity: {complexity_rating}."
    if errors:
        names = ", ".join(e.title for e in errors[:3])
        return f"Found {len(errors)} real bug(s): {names}. Lower score is expected until fixed."
    return f"No critical bugs — {len(warnings)} warning(s) to review. Score: {score}/100."


def critical_findings(issues: list[Issue], limit: int = 5) -> list[str]:
    findings: list[str] = []
    for i in sort_issues(issues):
        if i.severity == Severity.ERROR:
            loc = f"Line {i.line}: " if i.line else ""
            findings.append(f"{loc}{i.title} — {i.message}")
        if len(findings) >= limit:
            break
    return findings


def compute_score(issues: list[Issue], best_practices: list[Issue]) -> int:
    """Score reflects real bugs first; style/optional notes have smaller impact."""
    score = 100
    for i in issues:
        if i.severity == Severity.ERROR:
            score -= 18
        elif i.severity == Severity.WARNING:
            score -= 6
        elif i.severity == Severity.INFO:
            score -= 1
    for bp in best_practices:
        if bp.severity == Severity.WARNING:
            score -= 2
    return max(0, min(100, score))


def refine_review(response: ReviewResponse) -> ReviewResponse:
    issues = sort_issues(filter_noise(dedupe_issues(response.issues)))
    best_practices = sort_issues(dedupe_issues(response.best_practices))
    score = compute_score(issues, best_practices)

    return response.model_copy(
        update={
            "issues": issues,
            "best_practices": best_practices,
            "optimizations": response.optimizations[:8],
            "score": score,
            "critical_findings": critical_findings(issues),
            "issue_stats": count_by_severity(issues + best_practices),
            "summary": build_executive_summary(
                score, issues, response.complexity.rating, best_practices
            ),
        }
    )
