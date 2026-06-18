from app.analyzers.deep_rules import run_deep_analysis
from app.analyzers.registry import get_analyzer
from app.schemas import Language, ReviewRequest, ReviewResponse
from app.services.analysis_pipeline import refine_review

ENGINE_NAME = "CodeReview Engine v1"
ENGINE_VERSION = "1.0.0"

LINT_ENGINES: dict[Language, str] = {
    Language.PYTHON: "Ruff + AST",
    Language.JAVASCRIPT: "ESLint + Deep Rules",
    Language.TYPESCRIPT: "TypeScript-ESLint + Deep Rules",
    Language.JAVA: "Java Deep Analyzer",
    Language.CPP: "C++ Deep Analyzer",
}


async def run_review(request: ReviewRequest) -> ReviewResponse:
    analyzer = get_analyzer(request.language)
    issues, complexity, optimizations, best_practices, passed = analyzer.analyze(request.code)

    deep_issues, deep_bp, deep_passed = run_deep_analysis(request.code, request.language)
    issues.extend(deep_issues)
    best_practices.extend(deep_bp)
    passed.extend(deep_passed)
    passed.append(f"Analysis engine: {ENGINE_NAME} (offline, no API)")

    response = ReviewResponse(
        language=request.language,
        score=0,
        summary="",
        issues=issues,
        complexity=complexity,
        optimizations=optimizations,
        best_practices=best_practices,
        passed_checks=passed,
        analysis_engine="static",
        lint_engine=LINT_ENGINES.get(request.language, ENGINE_NAME),
    )
    return refine_review(response)


def review_to_json(review: ReviewResponse) -> str:
    return review.model_dump_json()
