import ast
import re

from app.analyzers.base import BaseAnalyzer
from app.engines.finding_router import linter_failure_issue, route_linter_finding
from app.engines.linter_runner import run_ruff
from app.schemas import (
    ComplexityMetric,
    Issue,
    IssueCategory,
    Language,
    OptimizationSuggestion,
    Severity,
)


class PythonAnalyzer(BaseAnalyzer):
    language = Language.PYTHON

    BAD_NAME_PATTERN = re.compile(r"^(l|O|I|tmp|temp|data|val|x|y|z|foo|bar)$", re.I)
    SINGLE_LETTER = re.compile(r"^[a-z]$", re.I)

    def analyze(
        self, code: str
    ) -> tuple[list[Issue], ComplexityMetric, list[OptimizationSuggestion], list[Issue], list[str]]:
        issues: list[Issue] = []
        optimizations: list[OptimizationSuggestion] = []
        best_practices: list[Issue] = []
        passed: list[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(
                Issue(
                    category=IssueCategory.SYNTAX,
                    severity=Severity.ERROR,
                    title="Syntax Error",
                    message=str(e.msg or e),
                    line=e.lineno,
                    column=e.offset,
                    suggestion="Fix the syntax error before running further analysis.",
                )
            )
            empty = ComplexityMetric(
                cyclomatic_complexity=0,
                lines_of_code=len(code.splitlines()),
                function_count=0,
                max_function_lines=0,
                max_nesting_depth=0,
                rating="unknown",
                details=["Cannot compute complexity due to syntax errors."],
            )
            return issues, empty, optimizations, best_practices, passed

        passed.append("Valid Python syntax")
        lines = code.splitlines()
        loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        func_count = len(functions)
        max_func_lines = 0
        max_nesting = 0
        total_cyclomatic = 0

        max_cc = 0
        for func in functions:
            start = func.lineno
            end = getattr(func, "end_lineno", start)
            func_lines = end - start + 1
            max_func_lines = max(max_func_lines, func_lines)
            cc = self._cyclomatic_complexity(func)
            total_cyclomatic += cc
            max_cc = max(max_cc, cc)
            nesting = self._max_nesting(func)
            max_nesting = max(max_nesting, nesting)

            if func_lines > 50:
                best_practices.append(
                    Issue(
                        category=IssueCategory.BEST_PRACTICE,
                        severity=Severity.WARNING,
                        title="Large Function",
                        message=f"Function '{func.name}' has {func_lines} lines. Consider splitting into smaller functions.",
                        line=start,
                        suggestion="Extract logical blocks into helper functions (Single Responsibility Principle).",
                    )
                )
            elif func_lines <= 30:
                passed.append(f"Function '{func.name}' has reasonable size ({func_lines} lines)")

            if cc > 10:
                issues.append(
                    Issue(
                        category=IssueCategory.COMPLEXITY,
                        severity=Severity.WARNING,
                        title="High Cyclomatic Complexity",
                        message=f"Function '{func.name}' has cyclomatic complexity {cc} (recommended ≤ 10).",
                        line=start,
                        suggestion="Reduce branching with early returns, guard clauses, or strategy pattern.",
                    )
                )

        avg_cc = total_cyclomatic // max(func_count, 1)
        report_cc = max_cc if func_count else 0
        rating = self._complexity_rating(report_cc, max_func_lines, max_nesting)

        complexity = ComplexityMetric(
            cyclomatic_complexity=report_cc,
            lines_of_code=loc,
            function_count=func_count,
            max_function_lines=max_func_lines,
            max_nesting_depth=max_nesting,
            rating=rating,
            details=[
                f"Peak cyclomatic complexity: {report_cc} (avg {avg_cc})",
                f"Total functions: {func_count}",
                f"Largest function: {max_func_lines} lines",
                f"Max nesting depth: {max_nesting}",
                "Lint engine: Ruff",
            ],
        )

        # ── REAL LINTER: Ruff ──
        ruff_findings, ruff_passed, ruff_error = run_ruff(code)
        if ruff_error:
            issues.append(linter_failure_issue("Ruff", ruff_error))
        passed.extend(ruff_passed)

        for finding in ruff_findings:
            finding.title = finding.message.split(".")[0][:100]
            bucket, item = route_linter_finding(finding)
            if bucket == "optimizations":
                optimizations.append(item)
            elif bucket == "issues":
                issues.append(item)
            else:
                best_practices.append(item)

        optimizations.extend(self._detect_string_concat_ast(tree, lines))
        issues.extend(self._detect_range_len_ast(tree, lines))
        issues.extend(self._detect_infinite_loops(code))

        if not any(i.category == IssueCategory.INFINITE_LOOP for i in issues):
            passed.append("No infinite loop detected")
        if not ruff_findings:
            passed.append("Ruff static analysis: clean")

        return issues, complexity, optimizations, best_practices, passed

    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        return complexity

    def _max_nesting(self, node: ast.AST, depth: int = 0) -> int:
        max_d = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                max_d = max(max_d, self._max_nesting(child, depth + 1))
            else:
                max_d = max(max_d, self._max_nesting(child, depth))
        return max_d

    def _detect_string_concat_ast(self, tree: ast.AST, lines: list[str]) -> list[OptimizationSuggestion]:
        opts: list[OptimizationSuggestion] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        if isinstance(child.target, ast.Name):
                            snippet = lines[child.lineno - 1].strip() if child.lineno <= len(lines) else ""
                            opts.append(
                                OptimizationSuggestion(
                                    title="String += in loop (O(n²) memory)",
                                    description="Each += creates a new string object. Collect parts in a list, then ''.join().",
                                    impact="high",
                                    line=child.lineno,
                                    before=snippet,
                                    after="parts.append(str(item)); return ''.join(parts)",
                                )
                            )
                            return opts
                    if isinstance(child, ast.Assign):
                        if isinstance(child.value, ast.BinOp) and isinstance(child.value.op, ast.Add):
                            if isinstance(child.value.left, ast.Name) and isinstance(child.value.right, ast.Call):
                                if isinstance(child.value.right.func, ast.Name) and child.value.right.func.id == "str":
                                    snippet = lines[child.lineno - 1].strip() if child.lineno <= len(lines) else ""
                                    opts.append(
                                        OptimizationSuggestion(
                                            title="String concatenation in loop (O(n²))",
                                            description="Use list + join instead of repeated concatenation.",
                                            impact="high",
                                            line=child.lineno,
                                            before=snippet,
                                            after="parts.append(str(x)); result = ''.join(parts)",
                                        )
                                    )
                                    return opts
        return opts

    def _detect_range_len_ast(self, tree: ast.AST, lines: list[str]) -> list[Issue]:
        found: list[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                    if node.iter.args and isinstance(node.iter.args[0], ast.Call):
                        if isinstance(node.iter.args[0].func, ast.Name) and node.iter.args[0].func.id == "len":
                            snippet = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                            found.append(
                                Issue(
                                    category=IssueCategory.OPTIMIZATION,
                                    severity=Severity.WARNING,
                                    title="Use enumerate() instead of range(len())",
                                    message="`for i in range(len(x))` is an anti-pattern — use `for i, item in enumerate(x)`.",
                                    line=node.lineno,
                                    suggestion="Replace with: `for i, item in enumerate(items):`",
                                    confidence=0.96,
                                    code_snippet=snippet,
                                )
                            )
        return found

    def _detect_infinite_loops(self, code: str) -> list[Issue]:
        found: list[Issue] = []
        for m in re.finditer(r"while\s+(True|1)\s*:", code):
            line_num = code[: m.start()].count("\n") + 1
            after = code[m.end() : m.end() + 500]
            if "break" not in after and "return" not in after:
                found.append(
                    Issue(
                        category=IssueCategory.INFINITE_LOOP,
                        severity=Severity.ERROR,
                        title="Infinite Loop",
                        message="`while True` (or `while 1`) has no break/return in the following block.",
                        line=line_num,
                        suggestion="Add a break/return or replace with a bounded loop.",
                        confidence=0.98,
                        code_snippet=code.splitlines()[line_num - 1].strip(),
                    )
                )
        return found
