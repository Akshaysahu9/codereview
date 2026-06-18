"""Verify real linters detect sample bugs."""
from app.schemas import Language
from app.analyzers.registry import get_analyzer

JS = """function findUser(users, id) {
  for (let i = 0; i < users.length; i++) {
    if (users[i].id = id) {
      return users[i].name;
    }
  }
  return null;
}

function pollServer() {
  while (true) {
    fetch("/api/status").then(r => r.json()).then(console.log);
  }
}
"""

PY = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

def process_data(items):
    result = ""
    for i in range(len(items)):
        x = items[i]
        result = result + str(x)
    return result
"""

TS = """interface User {
  id: number;
  name: string;
}

function getUser(users: User[], id: number): string | null {
  const user = users.find(u => u.id === id);
  return user.name;
}

const data: any = fetchData();
console.log(data.profile.email);
"""


def report(lang, code):
    a = get_analyzer(lang)
    issues, c, opts, bp, passed = a.analyze(code)
    print(f"\n=== {lang.value.upper()} ===")
    print(f"Issues: {len(issues)} | Optimizations: {len(opts)} | Best practices: {len(bp)}")
    for i in issues:
        print(f"  [{i.severity.value}] L{i.line} {i.title}")
        print(f"    {i.message[:100]}")
    for o in opts:
        print(f"  [OPT] L{o.line} {o.title}")
    for note in passed[:3]:
        print(f"  OK: {note}")


if __name__ == "__main__":
    report(Language.JAVASCRIPT, JS)
    report(Language.PYTHON, PY)
    report(Language.TYPESCRIPT, TS)
