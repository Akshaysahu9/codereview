"""Targeted code fixes based on detected issues — no blanket regex destruction."""

import re

from app.schemas import FixCodeResponse, Issue, IssueCategory, Language, Severity

_ASSIGN_IN_COND = re.compile(r"(?<![=!<>+\-*/%&|^:])=(?!=)")


def apply_smart_fix(code: str, language: Language, issues: list[Issue]) -> FixCodeResponse:
    if language == Language.PYTHON:
        return _fix_python(code, issues)
    if language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return _fix_js_ts(code, language, issues)
    if language == Language.JAVA:
        return _fix_java(code, issues)
    return _fix_cpp(code, issues)


def _fix_assignment_in_condition(line: str, comparator: str) -> str:
    m = re.search(r"if\s*\((.+)\)", line)
    if not m:
        return line
    condition = m.group(1)
    fixed = _ASSIGN_IN_COND.sub(comparator, condition, count=1)
    return line.replace(condition, fixed, 1)


def _fix_python(code: str, issues: list[Issue]) -> FixCodeResponse:
    lines = code.splitlines(keepends=True)
    changes: list[str] = []
    addressed = 0

    for issue in issues:
        if not issue.line or issue.line > len(lines):
            continue
        idx = issue.line - 1
        title = (issue.title or "").lower()

        if issue.category == IssueCategory.INFINITE_LOOP or "infinite" in title:
            if "while True" in lines[idx] or "while 1" in lines[idx]:
                indent = re.match(r"(\s*)", lines[idx]).group(1)
                lines.insert(idx + 1, f"{indent}    break  # TODO: replace with real exit condition\n")
                changes.append(f"Added break guard in infinite loop at line {issue.line}")
                addressed += 1

        if "enumerate" in title or "range(len" in (issue.message or "").lower():
            old = lines[idx]
            m = re.search(r"for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)", old)
            if m:
                i_var, arr = m.group(1), m.group(2)
                indent = re.match(r"(\s*)", old).group(1)
                lines[idx] = f"{indent}for {i_var}, item in enumerate({arr}):\n"
                changes.append(f"Replaced range(len()) with enumerate at line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.SYNTAX and "missing semicolon" in title:
            if not lines[idx].rstrip().endswith(";"):
                lines[idx] = lines[idx].rstrip() + ";\n"
                changes.append(f"Added missing semicolon at line {issue.line}")
                addressed += 1

    fixed = "".join(lines)

    if not changes:
        changes.append("No automatic fixes applied — run Analyze first, then Fix on reported issues")

    return FixCodeResponse(fixed_code=fixed, changes_summary=changes, issues_addressed=addressed)


def _fix_js_ts(code: str, language: Language, issues: list[Issue]) -> FixCodeResponse:
    lines = code.splitlines(keepends=True)
    changes: list[str] = []
    addressed = 0

    for issue in issues:
        if not issue.line or issue.line > len(lines):
            continue
        idx = issue.line - 1
        title = (issue.title or "").lower()
        old = lines[idx]

        if issue.category in (IssueCategory.LOGIC, IssueCategory.RUNTIME) and (
            "cond assign" in title or "assignment" in title or "eqeqeq" in title
        ):
            new = _fix_assignment_in_condition(old, "===")
            if new != old:
                lines[idx] = new
                changes.append(f"Fixed assignment/comparison at line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.INFINITE_LOOP or "infinite" in title or "constant condition" in title:
            if "while" in old.lower():
                indent = re.match(r"(\s*)", old).group(1)
                lines.insert(idx + 1, f"{indent}  break; // TODO: add real exit condition\n")
                changes.append(f"Added break in infinite loop at line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.NULL_POINTER or "undefined" in title or "find" in title:
            new = re.sub(r"(\w+)\.find\(([^)]+)\)\.(\w+)", r"\1.find(\2)?.\3", old)
            new = re.sub(r"return\s+(\w+)\.find\(([^)]+)\)\.(\w+)", r"const _u = \1.find(\2); return _u?.\3", new)
            if new != old:
                lines[idx] = new
                changes.append(f"Added null-safe access at line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.SYNTAX and "syntax" in title:
            if old.rstrip().endswith(","):
                lines[idx] = old.rstrip()[:-1] + "\n"
                changes.append(f"Removed trailing comma causing syntax error at line {issue.line}")
                addressed += 1

    fixed = "".join(lines)
    if not changes:
        changes.append("No safe automatic fixes for these issues yet")

    return FixCodeResponse(fixed_code=fixed, changes_summary=changes, issues_addressed=addressed)


def _fix_java(code: str, issues: list[Issue]) -> FixCodeResponse:
    lines = code.splitlines(keepends=True)
    changes: list[str] = []
    addressed = 0

    for issue in issues:
        if not issue.line or issue.line > len(lines):
            continue
        idx = issue.line - 1
        title = (issue.title or "").lower()
        old = lines[idx]

        if "assignment in condition" in title:
            new = _fix_assignment_in_condition(old, "==")
            if new != old:
                lines[idx] = new
                changes.append(f"Fixed assignment in condition at line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.INFINITE_LOOP or "infinite" in title:
            indent = re.match(r"(\s*)", old).group(1)
            lines.insert(idx + 1, f"{indent}    break; // TODO: exit condition\n")
            changes.append(f"Added break in infinite loop at line {issue.line}")
            addressed += 1

        if "missing semicolon" in title and not old.rstrip().endswith(";"):
            lines[idx] = old.rstrip() + ";\n"
            changes.append(f"Added semicolon at line {issue.line}")
            addressed += 1

        if "stringbuilder" in title.lower() or "string concatenation" in title.lower():
            block_start = max(0, idx - 5)
            for j in range(block_start, min(len(lines), idx + 20)):
                if 'String result = ""' in lines[j] or 'String result=""' in lines[j]:
                    indent = re.match(r"(\s*)", lines[j]).group(1)
                    lines[j] = f"{indent}StringBuilder result = new StringBuilder();\n"
                    changes.append("Replaced String with StringBuilder for loop concatenation")
                    addressed += 1
                    break

    return FixCodeResponse(
        fixed_code="".join(lines),
        changes_summary=changes or ["No automatic Java fixes matched — edit manually using suggestions"],
        issues_addressed=addressed,
    )


def _fix_cpp(code: str, issues: list[Issue]) -> FixCodeResponse:
    lines = code.splitlines(keepends=True)
    changes: list[str] = []
    addressed = 0

    for issue in issues:
        if not issue.line or issue.line > len(lines):
            continue
        idx = issue.line - 1
        title = (issue.title or "").lower()
        old = lines[idx]

        if "assignment in condition" in title:
            new = _fix_assignment_in_condition(old, "==")
            if new != old:
                lines[idx] = new
                changes.append(f"Fixed assignment in condition at line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.NULL_POINTER and "->" in old:
            m = re.search(r"(\w+)\s*->", old)
            if m:
                var = m.group(1)
                indent = re.match(r"(\s*)", old).group(1)
                lines.insert(idx, f"{indent}if ({var} == nullptr) return;\n")
                changes.append(f"Added nullptr guard before line {issue.line}")
                addressed += 1

        if issue.category == IssueCategory.INFINITE_LOOP or "infinite" in title:
            indent = re.match(r"(\s*)", old).group(1)
            lines.insert(idx + 1, f"{indent}    break; // TODO: exit condition\n")
            changes.append(f"Added break in infinite loop at line {issue.line}")
            addressed += 1

        if "missing semicolon" in title and not old.rstrip().endswith(";"):
            lines[idx] = old.rstrip() + ";\n"
            changes.append(f"Added semicolon at line {issue.line}")
            addressed += 1

    return FixCodeResponse(
        fixed_code="".join(lines),
        changes_summary=changes or ["No automatic C++ fixes matched — edit manually using suggestions"],
        issues_addressed=addressed,
    )
