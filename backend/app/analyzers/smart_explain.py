"""Code explanation using AST (Python) and pattern rules (other languages)."""

import ast
import re

from app.schemas import ExplainResponse, Language


def explain_code(code: str, language: Language) -> ExplainResponse:
    if language == Language.PYTHON:
        return _explain_python(code)
    if language == Language.JAVASCRIPT:
        return _explain_javascript(code)
    if language == Language.TYPESCRIPT:
        return _explain_typescript(code)
    if language == Language.JAVA:
        return _explain_java(code)
    return _explain_cpp(code)


def _explain_python(code: str) -> ExplainResponse:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return ExplainResponse(
            explanation=f"Code has a syntax error at line {e.lineno}: {e.msg}. Fix syntax before analysis.",
            key_concepts=["Syntax Error"],
        )

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    if not functions and not classes:
        return ExplainResponse(
            explanation="This Python snippet runs top-level statements — likely initialization or scripting logic.",
            time_complexity="O(n) depending on loops",
            space_complexity="O(1)",
            key_concepts=["Script", "Top-level execution"],
        )

    primary = functions[0]
    fname = primary.name
    concepts: list[str] = []
    explanation_parts: list[str] = []
    time_c = "O(n)"
    space_c = "O(1)"
    line_by_line: list[dict] = []

    body_nodes = list(ast.walk(primary))
    has_while = any(isinstance(n, ast.While) for n in body_nodes)
    has_for = any(isinstance(n, ast.For) for n in body_nodes)
    has_recursion = any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == fname
        for n in body_nodes
    )
    has_binary_search_pattern = _is_binary_search(primary)

    if has_binary_search_pattern:
        time_c = "O(log n)"
        space_c = "O(1)" if not has_recursion else "O(log n)"
        concepts.extend(["Binary Search", "Divide and Conquer", "Two Pointers"])
        explanation_parts.append(
            f"`{fname}()` implements binary search on a sorted sequence. "
            "Each iteration halves the search range using left/right pointers and a midpoint comparison."
        )
    elif has_recursion:
        time_c = "O(2^n) to O(n) depending on branching"
        space_c = "O(n) call stack depth"
        concepts.append("Recursion")
        explanation_parts.append(
            f"`{fname}()` uses recursion — each call pushes a new stack frame until a base case is reached."
        )
    elif has_while or has_for:
        concepts.append("Iterative Control Flow")
        explanation_parts.append(
            f"`{fname}()` uses iterative loops to process data element-by-element."
        )
        if has_for and any(isinstance(n, ast.ListComp) for n in body_nodes):
            concepts.append("List Comprehension")
            explanation_parts.append("Includes list comprehension for concise collection building.")

    args = [a.arg for a in primary.args.args]
    if args:
        explanation_parts.insert(
            0,
            f"Function `{fname}({', '.join(args)})` accepts {len(args)} parameter(s).",
        )

    if classes:
        concepts.append("Object-Oriented Programming")
        explanation_parts.append(f"Defines class `{classes[0].name}` with encapsulated behavior.")

    lines = code.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        desc = _describe_python_line(stripped, i + 1)
        if desc:
            line_by_line.append({"line": i + 1, "text": desc})
        if len(line_by_line) >= 15:
            break

    if not explanation_parts:
        explanation_parts.append(
            f"`{fname}()` performs computation on its inputs and returns a result based on conditional logic."
        )

    return ExplainResponse(
        explanation=" ".join(explanation_parts),
        time_complexity=time_c,
        space_complexity=space_c,
        key_concepts=concepts or ["Functions", "Control Flow"],
        line_by_line=line_by_line,
    )


def _is_binary_search(func: ast.FunctionDef) -> bool:
    names = {n.id for n in ast.walk(func) if isinstance(n, ast.Name)}
    has_left_right = "left" in names and "right" in names
    has_mid = "mid" in names
    has_while = any(isinstance(n, ast.While) for n in ast.walk(func))
    has_compare = any(isinstance(n, ast.Compare) for n in ast.walk(func))
    return has_left_right and has_mid and has_while and has_compare


def _describe_python_line(line: str, lineno: int) -> str | None:
    if line.startswith("def "):
        return f"Defines function {line.split('(')[0].replace('def ', '')}"
    if line.startswith("class "):
        return f"Defines class {line.split('(')[0].split(':')[0].replace('class ', '')}"
    if "while " in line:
        return "Loop — repeats until condition is false"
    if line.startswith("for ") or line.startswith("async for"):
        return "Iterates over a collection or range"
    if line.startswith("if ") or line.startswith("elif "):
        return "Conditional branch — executes block when condition is true"
    if line.startswith("return "):
        return f"Returns value to caller"
    if " = " in line and not line.startswith("if"):
        var = line.split("=")[0].strip()
        return f"Assigns/computes value for `{var}`"
    return None


def _explain_javascript(code: str) -> ExplainResponse:
    concepts: list[str] = []
    parts: list[str] = []
    time_c = "O(n)"
    space_c = "O(1)"

    fn = re.search(r"function\s+(\w+)", code)
    arrow = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(", code)
    name = (fn or arrow).group(1) if (fn or arrow) else "anonymous function"

    if re.search(r"while\s*\(\s*true\s*\)", code):
        concepts.append("Infinite Loop Risk")
        parts.append(f"`{name}` contains an infinite loop (`while(true)`) — typically used for polling/event loops.")
        time_c = "Unbounded"

    if re.search(r"if\s*\([^)]*\s=\s[^=]", code):
        concepts.extend(["Logic Bug", "Assignment vs Comparison"])
        parts.append(
            "Contains assignment (`=`) inside a condition instead of comparison (`===`) — "
            "this is a common bug that always evaluates truthy."
        )

    if "async" in code or "await" in code:
        concepts.append("Async/Await")
        parts.append("Uses asynchronous I/O — operations don't block the main thread.")
    if "fetch(" in code:
        concepts.append("HTTP / Fetch API")
        parts.append("Makes network requests via the Fetch API.")

    if re.search(r"for\s*\(", code):
        concepts.append("Iteration")
        if not parts:
            parts.append(f"`{name}` iterates over a collection with a for-loop — typically O(n) time.")

    line_by_line = _js_line_overview(code)
    return ExplainResponse(
        explanation=" ".join(parts) if parts else f"JavaScript function `{name}` processes input and returns output.",
        time_complexity=time_c,
        space_complexity=space_c,
        key_concepts=concepts or ["JavaScript", "Functions"],
        line_by_line=line_by_line,
    )


def _explain_typescript(code: str) -> ExplainResponse:
    base = _explain_javascript(code)
    concepts = list(base.key_concepts)
    parts = [base.explanation]

    if re.search(r":\s*any\b", code):
        concepts.append("Type Safety")
        parts.append("Uses `any` type which bypasses TypeScript's compile-time safety.")

    if ".find(" in code and re.search(r"\.find\([^)]+\)\.\w+", code):
        concepts.extend(["Optional Chaining", "Undefined Safety"])
        parts.append(
            "`.find()` returns `undefined` when no match — accessing properties directly can throw at runtime."
        )

    if "interface " in code or "type " in code:
        concepts.append("Type Definitions")

    return ExplainResponse(
        explanation=" ".join(parts),
        time_complexity=base.time_complexity,
        space_complexity=base.space_complexity,
        key_concepts=concepts,
        line_by_line=base.line_by_line,
    )


def _explain_java(code: str) -> ExplainResponse:
    concepts: list[str] = ["Static Typing", "JVM"]
    parts: list[str] = []

    cls = re.search(r"class\s+(\w+)", code)
    if cls:
        parts.append(f"Defines Java class `{cls.group(1)}` compiled to JVM bytecode.")

    if re.search(r"while\s*\(\s*true\s*\)", code):
        concepts.append("Infinite Loop")
        parts.append("Contains `while(true)` — intentional only for server/daemon loops with break conditions.")

    if re.search(r"=\s*\"\"\s*;", code) and "for " in code and "+ " in code:
        concepts.extend(["StringBuilder Pattern", "Performance"])
        parts.append(
            "String concatenation inside a loop creates new String objects each iteration — "
            "use StringBuilder for O(n) instead of O(n²)."
        )

    if "Integer.parseInt" in code:
        concepts.append("Exception Handling")
        parts.append("`Integer.parseInt` throws NumberFormatException on invalid input — wrap in try/catch.")

    return ExplainResponse(
        explanation=" ".join(parts) if parts else "Java class with methods following OOP conventions.",
        time_complexity="O(n) typical for linear loops",
        space_complexity="O(n) if building collections",
        key_concepts=concepts,
        line_by_line=_generic_line_overview(code),
    )


def _explain_cpp(code: str) -> ExplainResponse:
    concepts: list[str] = ["Manual Memory", "Compiled Language"]
    parts: list[str] = []

    if "new " in code:
        concepts.append("Dynamic Allocation")
        parts.append("Uses `new` for heap allocation — must pair with `delete` or use smart pointers.")
    if "-> " in code:
        parts.append("Pointer member access via `->` — dereferencing requires non-null pointer.")
    if "vector" in code.lower():
        concepts.append("STL Vector")

    return ExplainResponse(
        explanation=" ".join(parts) if parts else "C++ program with manual memory and STL containers.",
        time_complexity="O(n) to O(n log n) typical",
        space_complexity="O(n) for dynamic structures",
        key_concepts=concepts,
        line_by_line=_generic_line_overview(code),
    )


def _js_line_overview(code: str) -> list[dict]:
    result: list[dict] = []
    for i, line in enumerate(code.splitlines()):
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        if s.startswith("function ") or "=>" in s:
            result.append({"line": i + 1, "text": "Function declaration / arrow function"})
        elif s.startswith("if ") or s.startswith("} else"):
            result.append({"line": i + 1, "text": "Conditional branch"})
        elif s.startswith("for ") or s.startswith("while "):
            result.append({"line": i + 1, "text": "Loop construct"})
        elif s.startswith("return "):
            result.append({"line": i + 1, "text": "Return statement"})
        elif "fetch(" in s:
            result.append({"line": i + 1, "text": "Async HTTP request via fetch"})
        if len(result) >= 12:
            break
    return result


def _generic_line_overview(code: str) -> list[dict]:
    result: list[dict] = []
    for i, line in enumerate(code.splitlines()):
        s = line.strip()
        if s and not s.startswith("//") and not s.startswith("#"):
            result.append({"line": i + 1, "text": s[:100]})
        if len(result) >= 12:
            break
    return result
