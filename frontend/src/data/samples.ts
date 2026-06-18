import type { Language } from '../types';

export const SAMPLE_CODE: Record<Language, string> = {
  python: `def binary_search(arr, target):
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
`,

  javascript: `function findUser(users, id) {
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
`,

  typescript: `interface User {
  id: number;
  name: string;
}

function getUser(users: User[], id: number): string | null {
  const user = users.find(u => u.id === id);
  return user.name;
}

const data: any = fetchData();
console.log(data.profile.email);
`,

  java: `public class DataProcessor {
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
`,

  cpp: `#include <iostream>
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
`,
};

export const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
];
