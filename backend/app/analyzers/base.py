from abc import ABC, abstractmethod

from app.schemas import ComplexityMetric, Issue, Language, OptimizationSuggestion


class BaseAnalyzer(ABC):
    language: Language

    @abstractmethod
    def analyze(
        self, code: str
    ) -> tuple[list[Issue], ComplexityMetric, list[OptimizationSuggestion], list[Issue], list[str]]:
        """Returns issues, complexity, optimizations, best_practices, passed_checks."""
        ...

    def _score(
        self,
        issues: list[Issue],
        complexity: ComplexityMetric,
        best_practices: list[Issue],
    ) -> int:
        score = 100
        for issue in issues:
            if issue.severity == "error":
                score -= 15
            elif issue.severity == "warning":
                score -= 8
            else:
                score -= 3
        for bp in best_practices:
            if bp.severity == "warning":
                score -= 5
            else:
                score -= 2
        if complexity.rating == "high":
            score -= 10
        elif complexity.rating == "moderate":
            score -= 5
        return max(0, min(100, score))

    def _complexity_rating(self, cyclomatic: int, max_lines: int, nesting: int) -> str:
        if cyclomatic > 15 or max_lines > 80 or nesting > 5:
            return "high"
        if cyclomatic > 8 or max_lines > 40 or nesting > 3:
            return "moderate"
        return "low"
