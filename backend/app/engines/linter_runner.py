"""Run Ruff and ESLint on uploaded code snippets."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.schemas import Issue, IssueCategory, Language, Severity

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ESLINT_RUNNER = BACKEND_ROOT / "tools" / "eslint-runner"
TEMP_DIR = BACKEND_ROOT / ".analysis_tmp"
ESLINT_TEMP = ESLINT_RUNNER / ".lint_tmp"

for d in (TEMP_DIR, ESLINT_TEMP):
    d.mkdir(parents=True, exist_ok=True)


def _severity_from_ruff(code: str) -> Severity:
    if code.startswith(("E9", "F8", "F4")) or code in ("B006", "B007", "S307", "E722"):
        return Severity.ERROR
    if code.startswith(("E", "F", "B", "S", "RET")) or code.startswith("PERF"):
        return Severity.WARNING
    return Severity.INFO


def _category_from_ruff(code: str, message: str) -> IssueCategory:
    msg = message.lower()
    if code.startswith("S"):
        return IssueCategory.SECURITY
    if code.startswith("PERF") or "performance" in msg:
        return IssueCategory.OPTIMIZATION
    if code in ("B006", "B007", "B008"):
        return IssueCategory.LOGIC
    if code == "E722" or "bare except" in msg:
        return IssueCategory.BEST_PRACTICE
    if code.startswith("F841") or "unused" in msg:
        return IssueCategory.UNUSED
    if "infinite" in msg or code == "B023":
        return IssueCategory.INFINITE_LOOP
    if code.startswith("F") and "syntax" in msg:
        return IssueCategory.SYNTAX
    return IssueCategory.BEST_PRACTICE


def _suggestion_for_ruff(code: str, message: str) -> str | None:
    tips = {
        "B006": "Use `None` as default, then `items = [] if items is None else items` inside the function.",
        "E722": "Catch specific exceptions: `except ValueError:` instead of bare `except:`.",
        "F841": "Remove the unused variable or prefix with `_` if intentionally unused.",
        "PERF401": "Use a list comprehension instead of append-in-loop.",
        "PERF403": "Use a dict comprehension instead of manual loop.",
        "S307": "Never use eval() — use ast.literal_eval() or json.loads() for safe parsing.",
        "C416": "Use a list/dict/set comprehension instead of manual loop.",
        "SIM114": "Combine duplicate if branches with `or`.",
    }
    return tips.get(code)


def run_ruff(code: str) -> tuple[list[Issue], list[str], str | None]:
    """Run Ruff linter — same engine used by major Python projects."""
    passed: list[str] = []
    error_msg: str | None = None

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8", dir=str(TEMP_DIR)
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                tmp_path,
                "--output-format=json",
                "--config",
                str(BACKEND_ROOT / "pyproject.toml"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BACKEND_ROOT),
        )

        if not result.stdout.strip():
            passed.append("Ruff: no lint violations detected")
            return [], passed, None

        try:
            diagnostics = json.loads(result.stdout)
        except json.JSONDecodeError:
            return [], passed, result.stderr or "Ruff parse error"

        issues: list[Issue] = []
        for d in diagnostics:
            code_id = d.get("code", "RUF")
            message = d.get("message", "Lint violation")
            loc = d.get("location", {})
            row = loc.get("row")

            issues.append(
                Issue(
                    category=_category_from_ruff(code_id, message),
                    severity=_severity_from_ruff(code_id),
                    title=message.split(".")[0][:120],
                    message=f"[{code_id}] {message}",
                    line=row,
                    column=loc.get("column"),
                    suggestion=_suggestion_for_ruff(code_id, message) or d.get("fix", {}).get("message"),
                    confidence=0.99,
                    code_snippet=_line_at(code, row) if row else None,
                )
            )

        if not issues:
            passed.append("Ruff: code passes lint checks")
        return issues, passed, None

    except subprocess.TimeoutExpired:
        return [], [], "Ruff timed out"
    except FileNotFoundError:
        return [], [], "Ruff not installed — run: pip install ruff"
    finally:
        os.unlink(tmp_path)


def _line_at(code: str, line_num: int | None) -> str | None:
    if not line_num:
        return None
    lines = code.splitlines()
    if 1 <= line_num <= len(lines):
        return lines[line_num - 1].strip()
    return None


def _severity_from_eslint(rule_id: str, severity_num: int) -> Severity:
    if severity_num == 2:
        return Severity.ERROR
    if severity_num == 1:
        return Severity.WARNING
    return Severity.INFO


def _category_from_eslint(rule_id: str, message: str) -> IssueCategory:
    rules: dict[str, IssueCategory] = {
        "no-cond-assign": IssueCategory.LOGIC,
        "no-constant-condition": IssueCategory.INFINITE_LOOP,
        "eqeqeq": IssueCategory.LOGIC,
        "no-unused-vars": IssueCategory.UNUSED,
        "@typescript-eslint/no-explicit-any": IssueCategory.BEST_PRACTICE,
        "@typescript-eslint/no-unsafe-member-access": IssueCategory.NULL_POINTER,
        "@typescript-eslint/no-unsafe-call": IssueCategory.NULL_POINTER,
        "@typescript-eslint/strict-boolean-expressions": IssueCategory.LOGIC,
        "no-undef": IssueCategory.RUNTIME,
        "Parsing error": IssueCategory.SYNTAX,
    }
    if rule_id in rules:
        return rules[rule_id]
    if "null" in message.lower() or "undefined" in message.lower():
        return IssueCategory.NULL_POINTER
    return IssueCategory.BEST_PRACTICE


def _suggestion_for_eslint(rule_id: str) -> str | None:
    tips = {
        "no-cond-assign": "Use === for comparison: `if (users[i].id === id)` not `=` assignment.",
        "no-constant-condition": "Add a break/return condition or use setInterval for polling loops.",
        "eqeqeq": "Always use === and !== instead of == and !=.",
        "@typescript-eslint/no-explicit-any": "Replace `any` with a proper interface or `unknown`.",
        "@typescript-eslint/no-unsafe-member-access": "Add null check: `const u = users.find(...); if (!u) return null; return u.name;`",
        "no-undef": "Import or define the variable before use.",
    }
    return tips.get(rule_id)


def run_eslint(code: str, language: Language) -> tuple[list[Issue], list[str], str | None]:
    """Run ESLint for JS/TS files."""
    lint_script = ESLINT_RUNNER / "lint.mjs"
    if not lint_script.exists():
        return [], [], "ESLint runner not found — run: cd backend/tools/eslint-runner && npm install"

    ext = ".ts" if language == Language.TYPESCRIPT else ".js"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=ext, delete=False, encoding="utf-8", dir=str(ESLINT_TEMP)
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["node", str(lint_script), tmp_path, language.value],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=str(ESLINT_RUNNER),
        )

        if result.returncode not in (0, 1) and not result.stdout.strip():
            return [], [], result.stderr.strip() or "ESLint failed to run"

        if not result.stdout.strip():
            return [], ["ESLint: no violations detected"], None

        try:
            messages = json.loads(result.stdout)
        except json.JSONDecodeError:
            return [], [], result.stderr or "ESLint output parse error"

        if not isinstance(messages, list):
            messages = messages.get("results", [{}])[0].get("messages", [])

        issues: list[Issue] = []
        for m in messages:
            if m.get("severity", 0) == 0:
                continue
            rule_id = m.get("ruleId") or "lint"
            message = m.get("message", "Lint violation")
            line = m.get("line")

            if rule_id in ("null", "lint-error") or "parsing error" in message.lower():
                issues.append(
                    Issue(
                        category=IssueCategory.SYNTAX,
                        severity=Severity.ERROR,
                        title="Syntax Error",
                        message=message,
                        line=line,
                        column=m.get("column"),
                        suggestion="Fix the syntax error — analysis cannot run fully until this is corrected.",
                        confidence=0.99,
                        code_snippet=_line_at(code, line),
                    )
                )
                continue

            issues.append(
                Issue(
                    category=_category_from_eslint(rule_id, message),
                    severity=_severity_from_eslint(rule_id, m.get("severity", 1)),
                    title=rule_id.replace("@typescript-eslint/", "").replace("-", " ").title(),
                    message=message,
                    line=line,
                    column=m.get("column"),
                    suggestion=_suggestion_for_eslint(rule_id),
                    confidence=0.99,
                    code_snippet=_line_at(code, line),
                )
            )

        if not issues:
            return [], ["ESLint: code passes lint checks"], None
        return issues, [], None

    except subprocess.TimeoutExpired:
        return [], [], "ESLint timed out"
    except FileNotFoundError:
        return [], [], "Node.js not found — install Node.js for JS/TS analysis"
    finally:
        os.unlink(tmp_path)
