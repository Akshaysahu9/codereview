"""Full accuracy audit — expected vs actual for every sample."""
from app.schemas import Language, Severity
from app.analyzers.registry import get_analyzer
from app.services.review_service import run_review
from app.schemas import ReviewRequest
import asyncio

SAMPLES = {
    Language.PYTHON: '''def binary_search(arr, target):
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
''',
    Language.JAVASCRIPT: '''function findUser(users, id) {
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
''',
    Language.TYPESCRIPT: '''interface User {
  id: number;
  name: string;
}

function getUser(users: User[], id: number): string | null {
  const user = users.find(u => u.id === id);
  return user.name;
}

const data: any = fetchData();
console.log(data.profile.email);
''',
    Language.JAVA: '''public class DataProcessor {
    public String process(String input) {
        String result = "";
        for (int i = 0; i < input.length(); i++) {
            result = result + input.charAt(i);
        }
        return result;
    }

    public void runLoop() {
        while (true) {
            System.out.println("Running...");
        }
    }

    public int parse(String s) {
        return Integer.parseInt(s);
    }
}
''',
    Language.CPP: '''#include <iostream>
using namespace std;

int main() {
    int num;
    cout << "Enter a number: ";
    cin >> num;

    if (num % 2 == 0) {
        cout << num << " is Even." << endl;
    } else {
        cout << num << " is Odd." << endl;
    }
    return 0;
}
''',
}

# What MUST be detected (true positives)
MUST_FIND = {
    Language.PYTHON: ["range(len", "string", "concat", "enumerate", "PERF", "process_data"],
    Language.JAVASCRIPT: ["cond-assign", "assignment", "infinite", "while"],
    Language.TYPESCRIPT: ["find", "undefined", "any", "user"],
    Language.JAVA: ["infinite", "while", "StringBuilder", "parseInt", "parse"],
    Language.CPP: [],  # clean code — should find NOTHING critical
}

# What must NOT appear (false positives)
MUST_NOT = {
    Language.PYTHON: [],
    Language.JAVASCRIPT: [],
    Language.TYPESCRIPT: [],
    Language.JAVA: [],
    Language.CPP: ["assignment", "==", "instead of"],
}


async def main():
    for lang, code in SAMPLES.items():
        req = ReviewRequest(code=code, language=lang)
        r = await run_review(req)
        all_text = " ".join(
            f"{i.title} {i.message}" for i in r.issues + r.best_practices
        ).lower()
        opt_text = " ".join(o.title + o.description for o in r.optimizations).lower()
        combined = all_text + " " + opt_text

        print(f"\n{'='*60}")
        print(f"{lang.value.upper()} | Score: {r.score} | Engine: {r.lint_engine}")
        print(f"Issues({len(r.issues)}):")
        for i in r.issues:
            print(f"  [{i.severity.value}] L{i.line or '?'} {i.title}")
        print(f"Optimizations({len(r.optimizations)}):")
        for o in r.optimizations:
            print(f"  L{o.line or '?'} {o.title}")
        print(f"Best practices({len(r.best_practices)}):")
        for b in r.best_practices[:3]:
            print(f"  [{b.severity.value}] {b.title}")

        for kw in MUST_FIND.get(lang, []):
            ok = kw.lower() in combined
            print(f"  MUST FIND '{kw}': {'OK' if ok else 'MISSING'}")
        for kw in MUST_NOT.get(lang, []):
            bad = kw.lower() in combined
            print(f"  MUST NOT '{kw}': {'FAIL FALSE POSITIVE' if bad else 'OK'}")


if __name__ == "__main__":
    asyncio.run(main())
