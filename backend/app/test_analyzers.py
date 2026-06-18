"""Quick validation script — run: python -m app.test_analyzers"""

from app.analyzers.registry import get_analyzer
from app.schemas import Language

SAMPLES = {
    Language.PYTHON: """
def bad(x):
    while True:
        pass
    y = None
    return y.name
""",
    Language.JAVASCRIPT: """
function bug(users, id) {
  for (let i = 0; i < users.length; i++) {
    if (users[i].id = id) return users[i];
  }
}
while (true) { console.log("loop"); }
""",
}


def main():
    for lang, code in SAMPLES.items():
        analyzer = get_analyzer(lang)
        issues, complexity, opts, bp, passed = analyzer.analyze(code)
        score = analyzer._score(issues, complexity, bp)
        print(f"\n=== {lang.value.upper()} (score: {score}) ===")
        print(f"Issues: {len(issues)}, Best practices: {len(bp)}, Passed: {len(passed)}")
        for i in issues[:3]:
            print(f"  [{i.severity}] {i.title} (L{i.line})")


if __name__ == "__main__":
    main()
