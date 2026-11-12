"""Independent reference solutions, used only by the tests to validate the challenge data."""

PYTHON = {
    "sum-of-two": "a, b = map(int, input().split())\nprint(a + b)\n",
    "even-or-odd": "n = int(input())\nprint('Even' if n % 2 == 0 else 'Odd')\n",
    "fizzbuzz": (
        "n = int(input())\n"
        "for i in range(1, n + 1):\n"
        "    print('FizzBuzz' if i % 15 == 0 else 'Fizz' if i % 3 == 0 else 'Buzz' if i % 5 == 0 else i)\n"
    ),
    "palindrome-check": "s = input().strip()\nprint('Yes' if s == s[::-1] else 'No')\n",
    "second-largest": "input()\nnums = list(map(int, input().split()))\nprint(sorted(set(nums))[-2])\n",
    "prime-count": """\
n = int(input())
sieve = [True] * (n + 1)
sieve[0:2] = [False] * min(2, n + 1)
for i in range(2, int(n ** 0.5) + 1):
    if sieve[i]:
        for j in range(i * i, n + 1, i):
            sieve[j] = False
print(sum(sieve))
""",
    "balanced-brackets": """\
s = input().strip()
pairs = {')': '(', ']': '[', '}': '{'}
stack = []
ok = True
for ch in s:
    if ch in '([{':
        stack.append(ch)
    elif not stack or stack.pop() != pairs[ch]:
        ok = False
        break
print('Balanced' if ok and not stack else 'Not balanced')
""",
    "longest-increasing-subsequence": """\
from bisect import bisect_left
input()
tails = []
for x in map(int, input().split()):
    i = bisect_left(tails, x)
    if i == len(tails):
        tails.append(x)
    else:
        tails[i] = x
print(len(tails))
""",
    "shortest-path-grid": """\
from collections import deque
r, c = map(int, input().split())
grid = [input().strip() for _ in range(r)]
for i in range(r):
    for j in range(c):
        if grid[i][j] == 'S':
            start = (i, j)
        if grid[i][j] == 'E':
            end = (i, j)
dist = {start: 0}
q = deque([start])
while q:
    x, y = q.popleft()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < r and 0 <= ny < c and grid[nx][ny] != '#' and (nx, ny) not in dist:
            dist[(nx, ny)] = dist[(x, y)] + 1
            q.append((nx, ny))
print(dist.get(end, -1))
""",
}

# Plausible-looking solutions that are wrong. The flag says whether they pass both samples, so only the
# hidden tests can reject them (which is what hidden tests are for).
WRONG_PYTHON = [
    ("sum-of-two", "a, b = map(int, input().split())\nprint(a + b if a + b >= 0 else 0)\n", True),
    # Mimics the classic C/Java mistake: a negative odd number has remainder -1, not 1.
    ("even-or-odd", "import math\nn = int(input())\nprint('Odd' if math.fmod(n, 2) == 1 else 'Even')\n", True),
    ("fizzbuzz", "n = int(input())\nfor i in range(1, n + 1):\n    print('Fizz' if i % 3 == 0 else 'Buzz' if i % 5 == 0 else 'FizzBuzz' if i % 15 == 0 else i)\n", True),
    ("palindrome-check", "s = input().strip()\nprint('Yes' if s[0] == s[-1] else 'No')\n", True),
    ("second-largest", """\
input()
first = second = -10**18
for x in map(int, input().split()):
    if x > first:
        second, first = first, x
    elif x > second:
        second = x
print(second)
""", False),
    ("prime-count", "n = int(input())\nprint(sum(all(i % d for d in range(2, i)) for i in range(2, n)))\n", True),
    ("balanced-brackets", """\
s = input().strip()
pairs = {')': '(', ']': '[', '}': '{'}
stack = []
ok = True
for ch in s:
    if ch in '([{':
        stack.append(ch)
    elif not stack or stack.pop() != pairs[ch]:
        ok = False
        break
print('Balanced' if ok else 'Not balanced')
""", True),
    ("longest-increasing-subsequence", """\
input()
nums = list(map(int, input().split()))
best = run = 1
for a, b in zip(nums, nums[1:]):
    run = run + 1 if b > a else 1
    best = max(best, run)
print(best)
""", False),
    ("shortest-path-grid", """\
from collections import deque
r, c = map(int, input().split())
grid = [input().strip() for _ in range(r)]
for i in range(r):
    for j in range(c):
        if grid[i][j] == 'S':
            start = (i, j)
        if grid[i][j] == 'E':
            end = (i, j)
dist = {start: 0}
q = deque([start])
while q:
    x, y = q.popleft()
    for dx, dy in ((1, 0), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < r and 0 <= ny < c and grid[nx][ny] != '#' and (nx, ny) not in dist:
            dist[(nx, ny)] = dist[(x, y)] + 1
            q.append((nx, ny))
print(dist.get(end, -1))
""", True),
]

C = {
    "sum-of-two": r"""
#include <stdio.h>
int main(void) { int a, b; scanf("%d %d", &a, &b); printf("%d\n", a + b); return 0; }
""",
    "even-or-odd": r"""
#include <stdio.h>
int main(void) { int n; scanf("%d", &n); printf("%s\n", n % 2 != 0 ? "Odd" : "Even"); return 0; }
""",
    "balanced-brackets": r"""
#include <stdio.h>
int main(void) {
    static char s[100005], st[100005];
    scanf("%100000s", s);
    int top = 0, ok = 1;
    for (int i = 0; s[i]; i++) {
        char ch = s[i];
        if (ch == '(' || ch == '[' || ch == '{') { st[top++] = ch; }
        else {
            if (top == 0) { ok = 0; break; }
            char o = st[--top];
            if ((ch == ')' && o != '(') || (ch == ']' && o != '[') || (ch == '}' && o != '{')) { ok = 0; break; }
        }
    }
    printf("%s\n", (ok && top == 0) ? "Balanced" : "Not balanced");
    return 0;
}
""",
}

# The classic C trap: n % 2 == 1 is false for negative odd numbers, because -3 % 2 is -1 in C.
WRONG_C_EVEN_ODD = r"""
#include <stdio.h>
int main(void) { int n; scanf("%d", &n); printf("%s\n", n % 2 == 1 ? "Odd" : "Even"); return 0; }
"""

JAVA = {
    "sum-of-two": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) { Scanner in = new Scanner(System.in); System.out.println(in.nextInt() + in.nextInt()); }
}
""",
    "even-or-odd": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) { Scanner in = new Scanner(System.in); System.out.println(in.nextInt() % 2 != 0 ? "Odd" : "Even"); }
}
""",
    "balanced-brackets": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        String s = new Scanner(System.in).next();
        char[] st = new char[s.length()];
        int top = 0;
        boolean ok = true;
        for (char ch : s.toCharArray()) {
            if (ch == '(' || ch == '[' || ch == '{') { st[top++] = ch; }
            else {
                if (top == 0) { ok = false; break; }
                char o = st[--top];
                if ((ch == ')' && o != '(') || (ch == ']' && o != '[') || (ch == '}' && o != '{')) { ok = false; break; }
            }
        }
        System.out.println(ok && top == 0 ? "Balanced" : "Not balanced");
    }
}
""",
}
