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


class CppAnalyzer(BaseAnalyzer):
    language = Language.CPP

    def analyze(
        self, code: str
    ) -> tuple[list[Issue], ComplexityMetric, list[OptimizationSuggestion], list[Issue], list[str]]:
        issues: list[Issue] = []
        optimizations: list[OptimizationSuggestion] = []
        best_practices: list[Issue] = []
        passed: list[str] = []

        syntax_issue = self._check_syntax(code)
        if syntax_issue:
            issues.append(syntax_issue)
            return issues, self._empty(code), optimizations, best_practices, passed

        quote_issue = detect_unclosed_quotes(code, "cpp")
        if quote_issue:
            issues.append(quote_issue)

        passed.append("Valid C++ syntax (balanced brackets)")
        lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("//")]
        loc = len(lines)
        functions = self._extract_functions(code)
        func_count = max(len(functions), 1)
        max_lines = max((f["lines"] for f in functions), default=loc)
        max_nesting = self._max_nesting(code)
        branches = len(re.findall(r"\b(if|else if|while|for)\b", code))
        cc = max(1, branches // func_count)

        complexity = ComplexityMetric(
            cyclomatic_complexity=cc,
            lines_of_code=loc,
            function_count=len(functions),
            max_function_lines=max_lines,
            max_nesting_depth=max_nesting,
            rating=self._complexity_rating(cc, max_lines, max_nesting),
            details=[
                f"Control-flow branches: {branches}",
                f"Functions: {len(functions)}",
                "Engine: C++ Deep Analyzer (syntax + memory + security rules)",
            ],
        )

        issues.extend(scan_assignment_in_conditions(code, "cpp"))
        issues.extend(detect_missing_semicolons(code, "cpp"))
        issues.extend(self._detect_null_pointer(code))
        issues.extend(self._detect_infinite_loops(code))
        issues.extend(self._detect_runtime_issues(code))
        optimizations.extend(self._detect_optimizations(code))
        best_practices.extend(self._check_memory(code))

        if not issues:
            passed.append("No bugs detected in control flow or memory")
        if "==" in code and not any(i.title == "Assignment in Condition" for i in issues):
            passed.append("Comparison operators used correctly (== / !=)")

        return issues, complexity, optimizations, best_practices, passed

    def _empty(self, code: str) -> ComplexityMetric:
        return ComplexityMetric(
            cyclomatic_complexity=0,
            lines_of_code=len(code.splitlines()),
            function_count=0,
            max_function_lines=0,
            max_nesting_depth=0,
            rating="unknown",
            details=[],
        )

    def _check_syntax(self, code: str) -> Issue | None:
        if code.count("{") != code.count("}"):
            return Issue(
                category=IssueCategory.SYNTAX,
                severity=Severity.ERROR,
                title="Unbalanced Braces",
                message="Mismatched `{` and `}` in C++ code.",
                confidence=0.99,
            )
        if code.count("(") != code.count(")"):
            return Issue(
                category=IssueCategory.SYNTAX,
                severity=Severity.ERROR,
                title="Unbalanced Parentheses",
                message="Mismatched parentheses in C++ code.",
                confidence=0.99,
            )
        return None

    def _extract_functions(self, code: str) -> list[dict]:
        functions = []
        lines = code.splitlines()
        pattern = re.compile(r"^\s*(?:[\w:<>,\s*&]+\s+)?(\w+)\s*\([^;]*\)\s*\{?\s*$")
        skip = {"if", "for", "while", "switch", "catch", "else"}
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if m and m.group(1) not in skip:
                functions.append({"name": m.group(1), "line": i + 1, "lines": self._count_block_lines(lines, i)})
        if not functions and "int main" in code:
            for i, line in enumerate(lines):
                if "main(" in line:
                    functions.append({"name": "main", "line": i + 1, "lines": len(lines) - i})
                    break
        return functions

    def _count_block_lines(self, lines: list[str], start: int) -> int:
        brace = 0
        started = False
        count = 0
        for j in range(start, min(start + 300, len(lines))):
            count += 1
            brace += lines[j].count("{") - lines[j].count("}")
            if "{" in lines[j]:
                started = True
            if started and brace <= 0:
                break
        return count

    def _max_nesting(self, code: str) -> int:
        depth = max_d = 0
        for ch in code:
            if ch == "{":
                depth += 1
                max_d = max(max_d, depth)
            elif ch == "}":
                depth -= 1
        return max_d

    def _detect_null_pointer(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        for i, line in enumerate(code.splitlines(), 1):
            if "->" not in line:
                continue
            m = re.search(r"(\w+)\s*->", line)
            if not m:
                continue
            var = m.group(1)
            if var in ("this", "nullptr"):
                continue
            block_before = "\n".join(code.splitlines()[max(0, i - 4) : i - 1])
            if f"{var} != nullptr" not in block_before and f"{var} == nullptr" not in block_before:
                if "nullptr" in line or "= nullptr" in code:
                    found.append(
                        Issue(
                            category=IssueCategory.NULL_POINTER,
                            severity=Severity.ERROR,
                            title="Null Pointer Dereference",
                            message=f"Dereferencing `{var}` via `->` without a nullptr guard.",
                            line=i,
                            suggestion=f"Add `if ({var} != nullptr)` before accessing members.",
                            confidence=0.96,
                            code_snippet=line.strip(),
                        )
                    )
        return found

    def _detect_infinite_loops(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        for m in re.finditer(r"while\s*\(\s*true\s*\)", code, re.I):
            line_num = code[: m.start()].count("\n") + 1
            brace = code.find("{", m.end())
            if brace == -1:
                continue
            depth = 0
            end = brace
            for j in range(brace, min(brace + 500, len(code))):
                if code[j] == "{":
                    depth += 1
                elif code[j] == "}":
                    depth -= 1
                    if depth == 0:
                        end = j
                        break
            block = code[brace : end + 1]
            if "break" not in block and "return" not in block:
                found.append(
                    Issue(
                        category=IssueCategory.INFINITE_LOOP,
                        severity=Severity.ERROR,
                        title="Infinite Loop",
                        message="`while(true)` has no break or return in its body.",
                        line=line_num,
                        suggestion="Add an exit condition or use a bounded loop.",
                        confidence=0.98,
                        code_snippet=code.splitlines()[line_num - 1].strip(),
                    )
                )
        return found

    def _detect_runtime_issues(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        if re.search(r'scanf\s*\(\s*"%s"', code):
            found.append(
                Issue(
                    category=IssueCategory.RUNTIME,
                    severity=Severity.ERROR,
                    title="Buffer Overflow Risk",
                    message="`scanf(\"%s\")` has no length limit.",
                    suggestion="Use `%99s` width or `fgets()`.",
                    confidence=0.99,
                )
            )
        if "gets(" in code:
            found.append(
                Issue(
                    category=IssueCategory.RUNTIME,
                    severity=Severity.ERROR,
                    title="Unsafe gets()",
                    message="`gets()` is removed in C11 — buffer overflow risk.",
                    suggestion="Use `fgets()` instead.",
                    confidence=0.99,
                )
            )
        return found

    def _detect_optimizations(self, code: str) -> list[OptimizationSuggestion]:
        opts: list[OptimizationSuggestion] = []
        in_loop = bool(re.search(r"\b(for|while)\s*\(", code))
        if in_loop and "endl" in code and code.count("endl") >= 2:
            opts.append(
                OptimizationSuggestion(
                    title="Avoid endl inside loops",
                    description="`endl` flushes the buffer each call — use `\\n` in hot loops.",
                    impact="low",
                    before="cout << x << endl;",
                    after="cout << x << '\\n';",
                )
            )
        return opts

    def _check_memory(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        new_count = len(re.findall(r"\bnew\b", code))
        delete_count = len(re.findall(r"\bdelete\b", code))
        if new_count > delete_count:
            found.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.WARNING,
                    title="Possible Memory Leak",
                    message=f"{new_count} `new` vs {delete_count} `delete` — potential leak.",
                    suggestion="Prefer `std::unique_ptr` or match every `new` with `delete`.",
                    confidence=0.9,
                )
            )
        return found
