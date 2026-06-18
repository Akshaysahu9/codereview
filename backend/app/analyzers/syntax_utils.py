"""Basic syntax checks shared by Java and C++ analyzers."""

import re

from app.schemas import Issue, IssueCategory, Severity


def detect_unclosed_quotes(code: str, language: str) -> Issue | None:
    lines = code.splitlines()
    in_block_comment = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if language == "java" and stripped.startswith("/*"):
            in_block_comment = True
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("//"):
            continue

        no_line_comment = stripped.split("//")[0]
        dq = no_line_comment.count('"') - no_line_comment.count('\\"')
        sq = no_line_comment.count("'") - no_line_comment.count("\\'")
        if dq % 2 == 1 or sq % 2 == 1:
            return Issue(
                category=IssueCategory.SYNTAX,
                severity=Severity.ERROR,
                title="Unclosed String Literal",
                message="A string quote is not closed on this line.",
                line=i,
                suggestion="Add the missing closing quote.",
                confidence=0.95,
                code_snippet=stripped[:120],
            )
    return None


def detect_missing_semicolons(code: str, language: str) -> list[Issue]:
    """Flag obvious missing semicolons on statement-like lines."""
    found: list[Issue] = []
    call_patterns = [
        (r"(System\.out\.println\s*\([^)]*\))", "java"),
        (r"(return\s+[^;{}]+)", "java"),
        (r"(cout\s*<<[^;{}]+)", "cpp"),
        (r"(cin\s*>>[^;{}]+)", "cpp"),
    ]

    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue

        for pattern, lang in call_patterns:
            if lang != language:
                continue
            for m in re.finditer(pattern, stripped):
                rest = stripped[m.end() :].lstrip()
                if rest.startswith(";"):
                    continue
                if rest.startswith("}"):
                    found.append(
                        Issue(
                            category=IssueCategory.SYNTAX,
                            severity=Severity.ERROR,
                            title="Missing Semicolon",
                            message="Statement ends without `;` before the closing brace.",
                            line=i,
                            suggestion="Add `;` after the statement.",
                            confidence=0.92,
                            code_snippet=m.group(1)[:120],
                        )
                    )
                    break
                if not rest or rest[0] not in ";}":
                    found.append(
                        Issue(
                            category=IssueCategory.SYNTAX,
                            severity=Severity.ERROR,
                            title="Missing Semicolon",
                            message="This statement does not end with `;`.",
                            line=i,
                            suggestion="Add a semicolon at the end of the statement.",
                            confidence=0.9,
                            code_snippet=m.group(1)[:120],
                        )
                    )
                    break
    return found
