"""Extra static checks shared across languages."""

import re

from app.schemas import Issue, IssueCategory, Language, Severity

_HARDCODED_SECRET = re.compile(
    r"(password|passwd|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]",
    re.I,
)


def run_deep_analysis(code: str, language: Language) -> tuple[list[Issue], list[Issue], list[str]]:
    """Return extra issues, best_practices, passed notes."""
    issues: list[Issue] = []
    best: list[Issue] = []
    passed: list[str] = []

    for i, line in enumerate(code.splitlines(), 1):
        if _HARDCODED_SECRET.search(line):
            issues.append(
                Issue(
                    category=IssueCategory.SECURITY,
                    severity=Severity.ERROR,
                    title="Hardcoded Secret",
                    message="Credentials or tokens should not be stored in source code.",
                    line=i,
                    suggestion="Use environment variables or a secrets manager.",
                    confidence=0.95,
                    code_snippet=line.strip()[:100],
                )
            )

    if language == Language.PYTHON:
        issues.extend(_python_deep(code))
    elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        issues.extend(_js_ts_deep(code, language))
    elif language == Language.JAVA:
        issues.extend(_java_deep(code))
    elif language == Language.CPP:
        issues.extend(_cpp_deep(code))

    if not any(i.severity == Severity.ERROR for i in issues):
        passed.append("Deep rule engine: no security or logic red flags")
    return issues, best, passed


def _python_deep(code: str) -> list[Issue]:
    found: list[Issue] = []
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if re.search(r"/\s*0\b|/\s*0\.0\b", s) and not s.startswith("#"):
            found.append(
                Issue(
                    category=IssueCategory.RUNTIME,
                    severity=Severity.ERROR,
                    title="Division by Zero",
                    message="Literal division by zero will raise ZeroDivisionError.",
                    line=i,
                    suggestion="Guard the divisor before dividing.",
                    confidence=0.99,
                    code_snippet=s,
                )
            )
        if re.match(r"except\s*:", s):
            found.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.WARNING,
                    title="Bare except",
                    message="Bare `except:` catches all exceptions including KeyboardInterrupt.",
                    line=i,
                    suggestion="Catch specific exceptions.",
                    confidence=0.94,
                    code_snippet=s,
                )
            )
        if "eval(" in s or "exec(" in s:
            found.append(
                Issue(
                    category=IssueCategory.SECURITY,
                    severity=Severity.ERROR,
                    title="Unsafe eval/exec",
                    message="`eval`/`exec` on untrusted input is a code injection risk.",
                    line=i,
                    suggestion="Use ast.literal_eval or structured parsing.",
                    confidence=0.97,
                    code_snippet=s,
                )
            )
    return found


def _js_ts_deep(code: str, language: Language) -> list[Issue]:
    found: list[Issue] = []
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if re.search(r"\bconsole\.log\s*\(", s):
            found.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.INFO,
                    title="Debug console.log",
                    message="Remove console.log before production deployment.",
                    line=i,
                    confidence=0.85,
                    code_snippet=s[:100],
                )
            )
        if re.search(r"==[^=]", s) and "===" not in s and "!==" not in s and "==" in s:
            if re.search(r"[^!=<>]==[^=]", s):
                found.append(
                    Issue(
                        category=IssueCategory.LOGIC,
                        severity=Severity.WARNING,
                        title="Loose Equality",
                        message="`==` performs type coercion — prefer `===` for predictable comparisons.",
                        line=i,
                        suggestion="Replace `==` with `===` (and `!=` with `!==`).",
                        confidence=0.9,
                        code_snippet=s[:100],
                    )
                )
        if "catch {}" in s.replace(" ", "") or "catch(e){}" in s.replace(" ", ""):
            found.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.WARNING,
                    title="Empty catch block",
                    message="Swallowing errors hides failures and makes debugging hard.",
                    line=i,
                    suggestion="Log the error or rethrow with context.",
                    confidence=0.92,
                    code_snippet=s[:100],
                )
            )
    return found


def _java_deep(code: str) -> list[Issue]:
    found: list[Issue] = []
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if re.search(r"catch\s*\([^)]+\)\s*\{\s*\}", s):
            found.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.WARNING,
                    title="Empty catch block",
                    message="Empty catch hides exceptions — at minimum log the error.",
                    line=i,
                    suggestion="Log with logger or wrap in a meaningful runtime exception.",
                    confidence=0.93,
                    code_snippet=s[:100],
                )
            )
        if re.search(r"public\s+static\s+void\s+main", s) and i == 1:
            pass
        if ".equals(" in s and "null.equals" in s.replace(" ", ""):
            found.append(
                Issue(
                    category=IssueCategory.NULL_POINTER,
                    severity=Severity.ERROR,
                    title="NullPointerException Risk",
                    message="Calling `.equals` on a literal null reference will crash.",
                    line=i,
                    suggestion="Use `Objects.equals(a, b)` or call equals on the non-null variable.",
                    confidence=0.96,
                    code_snippet=s[:100],
                )
            )
        if re.search(r"/\s*0\b", s):
            found.append(
                Issue(
                    category=IssueCategory.RUNTIME,
                    severity=Severity.ERROR,
                    title="Division by Zero",
                    message="Division by literal zero throws ArithmeticException.",
                    line=i,
                    confidence=0.99,
                    code_snippet=s[:100],
                )
            )
    return found


def _cpp_deep(code: str) -> list[Issue]:
    found: list[Issue] = []
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if s.startswith("using namespace std") and "#include" not in s:
            found.append(
                Issue(
                    category=IssueCategory.BEST_PRACTICE,
                    severity=Severity.WARNING,
                    title="using namespace std",
                    message="Global `using namespace std` pollutes scope and causes name conflicts.",
                    line=i,
                    suggestion="Qualify names (`std::cout`) or use a narrow using-declaration.",
                    confidence=0.88,
                    code_snippet=s[:100],
                )
            )
        if re.search(r"/\s*0\b", s):
            found.append(
                Issue(
                    category=IssueCategory.RUNTIME,
                    severity=Severity.ERROR,
                    title="Division by Zero",
                    message="Division by zero is undefined behavior in C++.",
                    line=i,
                    confidence=0.99,
                    code_snippet=s[:100],
                )
            )
        if "system(" in s:
            found.append(
                Issue(
                    category=IssueCategory.SECURITY,
                    severity=Severity.WARNING,
                    title="system() call",
                    message="`system()` executes shell commands — injection risk with user input.",
                    line=i,
                    suggestion="Use safer APIs or validate input strictly.",
                    confidence=0.9,
                    code_snippet=s[:100],
                )
            )
    return found
