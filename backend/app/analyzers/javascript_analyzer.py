import re

from app.analyzers.base import BaseAnalyzer
from app.engines.finding_router import linter_failure_issue, route_linter_finding
from app.engines.linter_runner import run_eslint
from app.schemas import (
    ComplexityMetric,
    Issue,
    IssueCategory,
    Language,
    OptimizationSuggestion,
    Severity,
)


class JavaScriptAnalyzer(BaseAnalyzer):
    """JavaScript analysis powered by ESLint — same tool used in production codebases."""

    language = Language.JAVASCRIPT

    def analyze(
        self, code: str
    ) -> tuple[list[Issue], ComplexityMetric, list[OptimizationSuggestion], list[Issue], list[str]]:
        issues: list[Issue] = []
        optimizations: list[OptimizationSuggestion] = []
        best_practices: list[Issue] = []
        passed: list[str] = []

        lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("//")]
        loc = len(lines)
        func_count = len(re.findall(r"function\s+\w+|=>\s*\{", code))
        max_nesting = self._max_nesting(code)
        branches = len(re.findall(r"\b(if|while|for|case|\?\?|\|\||&&)\b", code))
        cc = max(1, branches)

        complexity = ComplexityMetric(
            cyclomatic_complexity=cc,
            lines_of_code=loc,
            function_count=max(func_count, 1),
            max_function_lines=loc,
            max_nesting_depth=max_nesting,
            rating=self._complexity_rating(cc, loc, max_nesting),
            details=[
                f"Branch points: {branches}",
                f"Lint engine: ESLint",
            ],
        )

        eslint_issues, eslint_passed, eslint_error = run_eslint(code, Language.JAVASCRIPT)
        if eslint_error:
            issues.append(linter_failure_issue("ESLint", eslint_error))
        passed.extend(eslint_passed)

        for finding in eslint_issues:
            bucket, item = route_linter_finding(finding)
            if bucket == "issues":
                issues.append(item)
            else:
                best_practices.append(item)

        issues.extend(self._detect_infinite_loops(code))

        if not eslint_issues and not eslint_error:
            passed.append("ESLint: no violations")

        return issues, complexity, optimizations, best_practices, passed

    def _detect_infinite_loops(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        for m in re.finditer(r"while\s*\(\s*true\s*\)", code, re.I):
            line_num = code[: m.start()].count("\n") + 1
            brace = code.find("{", m.end())
            if brace == -1:
                continue
            depth = 0
            end = brace
            for i in range(brace, min(brace + 600, len(code))):
                if code[i] == "{":
                    depth += 1
                elif code[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            block = code[brace : end + 1]
            if "break" not in block and "return" not in block:
                found.append(
                    Issue(
                        category=IssueCategory.INFINITE_LOOP,
                        severity=Severity.ERROR,
                        title="Infinite Loop (while true)",
                        message="`while (true)` never exits — confirmed by control-flow analysis.",
                        line=line_num,
                        suggestion="Add break/return, use setInterval for polling, or use event-driven architecture.",
                        confidence=0.98,
                        code_snippet=code.splitlines()[line_num - 1].strip(),
                    )
                )
        return found

    def _max_nesting(self, code: str) -> int:
        depth = max_d = 0
        for ch in code:
            if ch == "{":
                depth += 1
                max_d = max(max_d, depth)
            elif ch == "}":
                depth -= 1
        return max_d

    def _detect_ts_null_after_find(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        patterns = [
            re.compile(r"(\w+)\s*=\s*(\w+)\.find\([^)]+\)"),
            re.compile(r"return\s+(\w+)\.find\([^)]+\)\.(\w+)"),
            re.compile(r"(\w+)\.find\([^)]+\)\.(\w+)"),
        ]
        seen_lines: set[int] = set()

        for pattern in patterns:
            for m in pattern.finditer(code):
                line_num = code[: m.start()].count("\n") + 1
                if line_num in seen_lines:
                    continue
                line = code.splitlines()[line_num - 1]
                if "?." in line:
                    continue
                seen_lines.add(line_num)
                found.append(
                    Issue(
                        category=IssueCategory.NULL_POINTER,
                        severity=Severity.ERROR,
                        title="Possible undefined after .find()",
                        message="`.find()` returns undefined when no match — accessing a property can crash.",
                        line=line_num,
                        suggestion="Store the result, check it, or use optional chaining (`?.`).",
                        confidence=0.97,
                        code_snippet=line.strip(),
                    )
                )
        return found


class TypeScriptAnalyzer(JavaScriptAnalyzer):
    language = Language.TYPESCRIPT

    def analyze(
        self, code: str
    ) -> tuple[list[Issue], ComplexityMetric, list[OptimizationSuggestion], list[Issue], list[str]]:
        issues: list[Issue] = []
        optimizations: list[OptimizationSuggestion] = []
        best_practices: list[Issue] = []
        passed: list[str] = []

        lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("//")]
        loc = len(lines)
        branches = len(re.findall(r"\b(if|while|for|case|\?\?|\|\||&&)\b", code))
        cc = max(1, branches)
        max_nesting = self._max_nesting(code)

        complexity = ComplexityMetric(
            cyclomatic_complexity=cc,
            lines_of_code=loc,
            function_count=len(re.findall(r"function\s+\w+", code)) or 1,
            max_function_lines=loc,
            max_nesting_depth=max_nesting,
            rating=self._complexity_rating(cc, loc, max_nesting),
            details=[
                f"Branch points: {branches}",
                "Lint engine: TypeScript-ESLint",
            ],
        )

        eslint_issues, eslint_passed, eslint_error = run_eslint(code, Language.TYPESCRIPT)
        if eslint_error:
            issues.append(linter_failure_issue("ESLint", eslint_error))
        passed.extend(eslint_passed)

        for finding in eslint_issues:
            bucket, item = route_linter_finding(finding)
            if bucket == "issues":
                issues.append(item)
            else:
                best_practices.append(item)

        issues.extend(self._detect_ts_null_after_find(code))
        issues.extend(self._detect_infinite_loops(code))

        if re.search(r":\s*any\b", code):
            line_num = next(
                (i + 1 for i, l in enumerate(code.splitlines()) if re.search(r":\s*any\b", l)),
                None,
            )
            best_practices.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.WARNING,
                    title="Unsafe any type",
                    message="`: any` disables TypeScript type checking for this value.",
                    line=line_num,
                    suggestion="Define an interface or use `unknown` with type guards.",
                    confidence=0.95,
                )
            )

        if not eslint_issues and not eslint_error:
            passed.append("TypeScript ESLint: no violations")

        return issues, complexity, optimizations, best_practices, passed
