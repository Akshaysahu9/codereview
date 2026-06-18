"""Unit test scaffolds for common patterns."""

import re

from app.schemas import GenerateTestsResponse, Language


def generate_tests(code: str, language: Language, framework: str | None = None) -> GenerateTestsResponse:
    defaults = {
        Language.PYTHON: "pytest",
        Language.JAVASCRIPT: "jest",
        Language.TYPESCRIPT: "jest",
        Language.JAVA: "junit5",
        Language.CPP: "gtest",
    }
    fw = framework or defaults[language]

    if language == Language.PYTHON:
        return _python_tests(code, fw)
    if language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return _js_tests(code, fw, language)
    if language == Language.JAVA:
        return _java_tests(code, fw)
    return _cpp_tests(code, fw)


def _python_tests(code: str, fw: str) -> GenerateTestsResponse:
    funcs = re.findall(r"def\s+(\w+)\s*\(([^)]*)\)", code)
    if not funcs:
        return GenerateTestsResponse(
            framework=fw,
            tests="# No functions found — add a function to generate tests.\n",
            test_count=0,
            coverage_notes=["Define at least one function to scaffold tests."],
        )

    name, args = funcs[0]
    params = [a.strip().split(":")[0].split("=")[0].strip() for a in args.split(",") if a.strip()]
    if "arr" in params or "items" in params or "nums" in params:
        happy = f"{name}([1, 2, 3, 4, 5], 3)"
        edge = f"{name}([], 1)"
    elif "target" in params:
        happy = f"{name}([1, 2, 3, 4, 5], 3)"
        edge = f"{name}([], 99)"
    else:
        happy = f"{name}({', '.join('1' for _ in params) if params else ''})"
        edge = f"{name}({', '.join('0' for _ in params) if params else ''})"

    tests = f'''import pytest

# from your_module import {name}


def test_{name}_happy_path():
    result = {happy}
    assert result is not None


def test_{name}_edge_case():
    result = {edge}
    assert result is not None or result == -1


def test_{name}_type_safety():
    with pytest.raises((TypeError, ValueError)):
        {name}(None)
'''
    return GenerateTestsResponse(
        framework=fw,
        tests=tests,
        test_count=3,
        coverage_notes=["Test scaffold — update imports and assertions for your module."],
    )


def _js_tests(code: str, fw: str, language: Language) -> GenerateTestsResponse:
    fn = re.search(r"function\s+(\w+)\s*\(([^)]*)\)", code)
    arrow = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|\w+)\s*=>", code)
    name = (fn or arrow).group(1) if (fn or arrow) else "targetFn"
    ext = "ts" if language == Language.TYPESCRIPT else "js"
    tests = f'''const {{ {name} }} = require("./module.{ext.replace('ts', 'js')}");

describe("{name}", () => {{
  test("returns expected result for valid input", () => {{
    expect({name}(/* args */)).toBeDefined();
  }});

  test("handles null/undefined safely", () => {{
    expect(() => {name}(null)).not.toThrow();
  }});

  test("edge case — empty input", () => {{
    expect({name}(/* empty */)).toBeDefined();
  }});
}});
'''
    return GenerateTestsResponse(
        framework=fw,
        tests=tests,
        test_count=3,
        coverage_notes=["Test scaffold — fill in realistic arguments."],
    )


def _java_tests(code: str, fw: str) -> GenerateTestsResponse:
    cls = re.search(r"class\s+(\w+)", code)
    cname = cls.group(1) if cls else "Target"
    tests = f'''import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class {cname}Test {{

    @Test
    void happyPath() {{
        {cname} obj = new {cname}();
        assertNotNull(obj);
    }}

    @Test
    void edgeCaseNullInput() {{
        {cname} obj = new {cname}();
        assertDoesNotThrow(() -> obj.toString());
    }}
}}
'''
    return GenerateTestsResponse(
        framework=fw,
        tests=tests,
        test_count=2,
        coverage_notes=["Test scaffold — add method-specific assertions."],
    )


def _cpp_tests(code: str, fw: str) -> GenerateTestsResponse:
    tests = '''#include <gtest/gtest.h>

TEST(SampleSuite, BasicSanity) {
    EXPECT_EQ(1 + 1, 2);
}

TEST(SampleSuite, EdgeCase) {
    EXPECT_TRUE(true);
}
'''
    return GenerateTestsResponse(
        framework=fw,
        tests=tests,
        test_count=2,
        coverage_notes=["Test scaffold — link your functions and add cases."],
    )
