"""Accurate condition parsing — avoids false positives on ==, !=, <=, >=."""

import re

from app.schemas import Issue, IssueCategory, Severity

# Single `=` in a condition (not ==, !=, <=, >=, +=, etc.)
_ASSIGN_RE = re.compile(r"(?<![=!<>+\-*/%&|^:])=(?!=)")


def has_assignment_in_condition(line: str) -> bool:
    m = re.search(r"if\s*\((.+)\)", line)
    if not m:
        return False
    condition = m.group(1)
    return bool(_ASSIGN_RE.search(condition))


def scan_assignment_in_conditions(code: str, language: str) -> list[Issue]:
    found: list[Issue] = []
    for i, line in enumerate(code.splitlines(), 1):
        for m in re.finditer(r"if\s*\(([^)]+)\)", line):
            condition = m.group(1)
            if not _ASSIGN_RE.search(condition):
                continue
            found.append(
                Issue(
                    category=IssueCategory.LOGIC,
                    severity=Severity.ERROR,
                    title="Assignment in Condition",
                    message="Single `=` used inside `if` — this assigns a value instead of comparing.",
                    line=i,
                    suggestion="Use `==` for equality comparison, not `=` assignment.",
                    confidence=0.97,
                    code_snippet=line.strip(),
                )
            )
            break
    return found
