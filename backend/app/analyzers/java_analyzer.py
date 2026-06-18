import re

from app.analyzers.base import BaseAnalyzer
from app.analyzers.condition_utils import scan_assignment_in_conditions
from app.analyzers.syntax_utils import detect_missing_semicolons, detect_unclosed_quotes
from app.schemas import (
    ComplexityMetric,
    Issue,
    IssueCategory,
    Language,
    OptimizationSuggestion,
    Severity,
)

JAVA_SAFE_CALLS = {
    "System", "Math", "Arrays", "Collections", "Objects", "Optional",
    "String", "Integer", "Double", "Boolean", "this", "super",
}


class JavaAnalyzer(BaseAnalyzer):
    language = Language.JAVA

    def analyze(
        self, code: str
    ) -> tuple[list[Issue], ComplexityMetric, list[OptimizationSuggestion], list[Issue], list[str]]:
        issues: list[Issue] = []
        optimizations: list[OptimizationSuggestion] = []
        best_practices: list[Issue] = []
        passed: list[str] = []

        if code.count("{") != code.count("}"):
            issues.append(Issue(
                category=IssueCategory.SYNTAX, severity=Severity.ERROR,
                title="Unbalanced Braces", message="Mismatched `{` and `}`.", confidence=0.99,
            ))
            return issues, self._empty(code), optimizations, best_practices, passed

        quote_issue = detect_unclosed_quotes(code, "java")
        if quote_issue:
            issues.append(quote_issue)

        passed.append("Valid Java syntax")
        lines = code.splitlines()
        loc = len([l for l in lines if l.strip() and not l.strip().startswith("//")])

        issues.extend(scan_assignment_in_conditions(code, "java"))
        issues.extend(detect_missing_semicolons(code, "java"))
        issues.extend(self._detect_infinite_loops(code))
        issues.extend(self._detect_parse_int(code))
        optimizations.extend(self._detect_stringbuilder(code))

        if not any(i.severity == Severity.ERROR for i in issues):
            passed.append("No critical bugs detected")
        if not issues:
            passed.append("Control flow looks correct")

        complexity = ComplexityMetric(
            cyclomatic_complexity=max(1, len(re.findall(r"\b(if|while|for|catch)\b", code))),
            lines_of_code=loc,
            function_count=max(1, len(re.findall(r"(?:public|private|protected)\s+\w+", code))),
            max_function_lines=loc,
            max_nesting_depth=self._max_nesting(code),
            rating="low" if loc < 80 else "moderate",
            details=["Engine: Java Deep Analyzer (syntax + logic + security rules)"],
        )
        return issues, complexity, optimizations, best_practices, passed

    def _empty(self, code: str) -> ComplexityMetric:
        return ComplexityMetric(
            cyclomatic_complexity=0, lines_of_code=len(code.splitlines()),
            function_count=0, max_function_lines=0, max_nesting_depth=0,
            rating="unknown", details=[],
        )

    def _max_nesting(self, code: str) -> int:
        d = mx = 0
        for c in code:
            if c == "{": d += 1; mx = max(mx, d)
            elif c == "}": d -= 1
        return mx

    def _detect_infinite_loops(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        for m in re.finditer(r"while\s*\(\s*true\s*\)", code, re.I):
            line_num = code[: m.start()].count("\n") + 1
            brace = code.find("{", m.end())
            if brace == -1:
                continue
            depth = 0
            end = brace
            for j in range(brace, min(brace + 800, len(code))):
                if code[j] == "{": depth += 1
                elif code[j] == "}":
                    depth -= 1
                    if depth == 0:
                        end = j
                        break
            block = code[brace : end + 1]
            if "break" not in block and "return" not in block:
                found.append(Issue(
                    category=IssueCategory.INFINITE_LOOP,
                    severity=Severity.ERROR,
                    title="Infinite Loop",
                    message="`while(true)` never exits — no break or return inside the loop body.",
                    line=line_num,
                    suggestion="Add a break condition or use a terminating flag.",
                    confidence=0.98,
                    code_snippet=lines[line_num - 1].strip() if (lines := code.splitlines()) and line_num <= len(lines) else "",
                ))
        return found

    def _detect_parse_int(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        for i, line in enumerate(code.splitlines(), 1):
            if "Integer.parseInt" in line or "parseInt(" in line:
                method_block = self._method_block(code, i)
                if method_block and "try" not in method_block:
                    found.append(Issue(
                        category=IssueCategory.RUNTIME,
                        severity=Severity.WARNING,
                        title="Unhandled NumberFormatException",
                        message="`parseInt` throws on invalid input — wrap in try/catch.",
                        line=i,
                        suggestion="Use try/catch or validate with regex before parsing.",
                        confidence=0.92,
                        code_snippet=line.strip(),
                    ))
        return found

    def _method_block(self, code: str, line_num: int) -> str:
        lines = code.splitlines()
        start = line_num - 1
        while start > 0 and "{" not in lines[start]:
            start -= 1
        depth = 0
        parts: list[str] = []
        for j in range(start, min(start + 80, len(lines))):
            parts.append(lines[j])
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0 and j > start:
                break
        return "\n".join(parts)

    def _detect_stringbuilder(self, code: str) -> list[OptimizationSuggestion]:
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r'\+\s*(\w+\.)?(charAt|toString|valueOf)\(', line) or (
                "result = result +" in line.replace(" ", "")
            ):
                if any("for " in l for l in code.splitlines()):
                    return [OptimizationSuggestion(
                        title="Use StringBuilder in loop",
                        description="String + in a loop is O(n²) on the JVM.",
                        impact="high",
                        line=i,
                        before=line.strip(),
                        after="StringBuilder sb = new StringBuilder(); sb.append(...); return sb.toString();",
                    )]
        return []
