"""Independent reference solutions for the lesson exercises. Used only by tests."""

PYTHON = {
    "ex-c-product": "a, b = map(int, input().split())\nprint(a * b)\n",
    "ex-py-echo": "w = input().strip()\nprint(w, w)\n",
    "ex-java-square": "n = int(input())\nprint(n * n)\n",
    "ex-types-divmod": "a, b = map(int, input().split())\nprint(a // b, a % b)\n",
    "ex-conditionals-sign": "n = int(input())\nprint('Positive' if n > 0 else 'Negative' if n < 0 else 'Zero')\n",
    "ex-loops-sum": "n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    total += i\nprint(total)\n",
    "ex-functions-factorial": "def fact(n):\n    return 1 if n == 0 else n * fact(n - 1)\n\nprint(fact(int(input())))\n",
    "ex-arrays-max": "input()\nnums = list(map(int, input().split()))\nbest = nums[0]\nfor x in nums:\n    if x > best:\n        best = x\nprint(best)\n",
    "ex-strings-vowels": "s = input().strip().lower()\nprint(sum(1 for ch in s if ch in 'aeiou'))\n",
    "ex-ds-first-unique": (
        "s = input().strip()\ncounts = {}\nfor ch in s:\n    counts[ch] = counts.get(ch, 0) + 1\n"
        "for ch in s:\n    if counts[ch] == 1:\n        print(ch)\n        break\nelse:\n    print('none')\n"
    ),
    "ex-algo-sort": (
        "n = int(input())\nnums = list(map(int, input().split()))\n"
        "for i in range(n):\n    m = i\n    for j in range(i + 1, n):\n        if nums[j] < nums[m]:\n            m = j\n"
        "    nums[i], nums[m] = nums[m], nums[i]\nprint(*nums)\n"
    ),
    "ex-oop-rectangle": (
        "class Rectangle:\n    def __init__(self, w, h):\n        self.w = w\n        self.h = h\n"
        "    def area(self):\n        return self.w * self.h\n    def perimeter(self):\n        return 2 * (self.w + self.h)\n\n"
        "w, h = map(int, input().split())\nr = Rectangle(w, h)\nprint(r.area(), r.perimeter())\n"
    ),
}

C = {
    "ex-c-product": '#include <stdio.h>\nint main(void) {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d\\n", a * b);\n    return 0;\n}\n',
    "ex-py-echo": '#include <stdio.h>\nint main(void) {\n    char s[128];\n    scanf("%100s", s);\n    printf("%s %s\\n", s, s);\n    return 0;\n}\n',
    "ex-java-square": '#include <stdio.h>\nint main(void) {\n    int n;\n    scanf("%d", &n);\n    printf("%d\\n", n * n);\n    return 0;\n}\n',
    "ex-types-divmod": '#include <stdio.h>\nint main(void) {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d %d\\n", a / b, a % b);\n    return 0;\n}\n',
    "ex-conditionals-sign": '#include <stdio.h>\nint main(void) {\n    int n;\n    scanf("%d", &n);\n    puts(n > 0 ? "Positive" : n < 0 ? "Negative" : "Zero");\n    return 0;\n}\n',
    "ex-loops-sum": '#include <stdio.h>\nint main(void) {\n    int n, total = 0;\n    scanf("%d", &n);\n    for (int i = 1; i <= n; i++) total += i;\n    printf("%d\\n", total);\n    return 0;\n}\n',
    "ex-functions-factorial": '#include <stdio.h>\nint fact(int n) { return n == 0 ? 1 : n * fact(n - 1); }\nint main(void) {\n    int n;\n    scanf("%d", &n);\n    printf("%d\\n", fact(n));\n    return 0;\n}\n',
    "ex-arrays-max": '#include <stdio.h>\nint main(void) {\n    int n;\n    static int a[2005];\n    scanf("%d", &n);\n    for (int i = 0; i < n; i++) scanf("%d", &a[i]);\n    int best = a[0];\n    for (int i = 1; i < n; i++) if (a[i] > best) best = a[i];\n    printf("%d\\n", best);\n    return 0;\n}\n',
    "ex-strings-vowels": '#include <ctype.h>\n#include <stdio.h>\n#include <string.h>\nint main(void) {\n    char s[128];\n    int count = 0;\n    scanf("%100s", s);\n    for (int i = 0; s[i]; i++) if (strchr("aeiou", tolower((unsigned char)s[i]))) count++;\n    printf("%d\\n", count);\n    return 0;\n}\n',
    "ex-ds-first-unique": '#include <stdio.h>\nint main(void) {\n    char s[128];\n    int counts[256] = {0};\n    scanf("%100s", s);\n    for (int i = 0; s[i]; i++) counts[(unsigned char)s[i]]++;\n    for (int i = 0; s[i]; i++) {\n        if (counts[(unsigned char)s[i]] == 1) { printf("%c\\n", s[i]); return 0; }\n    }\n    printf("none\\n");\n    return 0;\n}\n',
    "ex-algo-sort": '#include <stdio.h>\nint main(void) {\n    int n;\n    static int a[2005];\n    scanf("%d", &n);\n    for (int i = 0; i < n; i++) scanf("%d", &a[i]);\n    for (int i = 0; i < n; i++) {\n        int m = i;\n        for (int j = i + 1; j < n; j++) if (a[j] < a[m]) m = j;\n        int t = a[i]; a[i] = a[m]; a[m] = t;\n    }\n    for (int i = 0; i < n; i++) printf(i ? " %d" : "%d", a[i]);\n    printf("\\n");\n    return 0;\n}\n',
    "ex-oop-rectangle": '#include <stdio.h>\nstruct Rectangle { long w, h; };\nlong area(struct Rectangle r) { return r.w * r.h; }\nlong perimeter(struct Rectangle r) { return 2 * (r.w + r.h); }\nint main(void) {\n    long w, h;\n    scanf("%ld %ld", &w, &h);\n    struct Rectangle r = {w, h};\n    printf("%ld %ld\\n", area(r), perimeter(r));\n    return 0;\n}\n',
}

_IN = "import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n"
_OUT = "    }\n}\n"

JAVA = {
    "ex-c-product": _IN + "        int a = in.nextInt(), b = in.nextInt();\n        System.out.println(a * b);\n" + _OUT,
    "ex-py-echo": _IN + "        String s = in.next();\n        System.out.println(s + \" \" + s);\n" + _OUT,
    "ex-java-square": _IN + "        int n = in.nextInt();\n        System.out.println(n * n);\n" + _OUT,
    "ex-types-divmod": _IN + "        int a = in.nextInt(), b = in.nextInt();\n        System.out.println((a / b) + \" \" + (a % b));\n" + _OUT,
    "ex-conditionals-sign": _IN + "        int n = in.nextInt();\n        System.out.println(n > 0 ? \"Positive\" : n < 0 ? \"Negative\" : \"Zero\");\n" + _OUT,
    "ex-loops-sum": _IN + "        int n = in.nextInt(), total = 0;\n        for (int i = 1; i <= n; i++) total += i;\n        System.out.println(total);\n" + _OUT,
    "ex-functions-factorial": "import java.util.Scanner;\n\npublic class Main {\n    static int fact(int n) {\n        return n == 0 ? 1 : n * fact(n - 1);\n    }\n\n    public static void main(String[] args) {\n        System.out.println(fact(new Scanner(System.in).nextInt()));\n    }\n}\n",
    "ex-arrays-max": _IN + "        int n = in.nextInt();\n        int best = in.nextInt();\n        for (int i = 1; i < n; i++) best = Math.max(best, in.nextInt());\n        System.out.println(best);\n" + _OUT,
    "ex-strings-vowels": _IN + "        String s = in.next().toLowerCase();\n        int count = 0;\n        for (char ch : s.toCharArray()) if (\"aeiou\".indexOf(ch) >= 0) count++;\n        System.out.println(count);\n" + _OUT,
    "ex-ds-first-unique": "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        String s = new Scanner(System.in).next();\n        Map<Character, Integer> counts = new HashMap<>();\n        for (char ch : s.toCharArray()) counts.merge(ch, 1, Integer::sum);\n        for (char ch : s.toCharArray()) {\n            if (counts.get(ch) == 1) {\n                System.out.println(ch);\n                return;\n            }\n        }\n        System.out.println(\"none\");\n    }\n}\n",
    "ex-algo-sort": _IN + "        int n = in.nextInt();\n        int[] a = new int[n];\n        for (int i = 0; i < n; i++) a[i] = in.nextInt();\n        for (int i = 0; i < n; i++) {\n            int m = i;\n            for (int j = i + 1; j < n; j++) if (a[j] < a[m]) m = j;\n            int t = a[i]; a[i] = a[m]; a[m] = t;\n        }\n        StringBuilder sb = new StringBuilder();\n        for (int i = 0; i < n; i++) sb.append(i > 0 ? \" \" : \"\").append(a[i]);\n        System.out.println(sb);\n" + _OUT,
    "ex-oop-rectangle": "import java.util.Scanner;\n\nclass Rectangle {\n    final long w, h;\n    Rectangle(long w, long h) { this.w = w; this.h = h; }\n    long area() { return w * h; }\n    long perimeter() { return 2 * (w + h); }\n}\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        Rectangle r = new Rectangle(in.nextLong(), in.nextLong());\n        System.out.println(r.area() + \" \" + r.perimeter());\n    }\n}\n",
}

# Plausible-but-wrong Python solutions: (exercise id, source, passes every sample test?)
WRONG = [
    ("ex-arrays-max", "input()\nnums = list(map(int, input().split()))\nbest = 0\nfor x in nums:\n    best = max(best, x)\nprint(best)\n", False),
    ("ex-ds-first-unique", "s = input().strip()\nprint(next((c for c in sorted(set(s)) if s.count(c) == 1), 'none'))\n", False),
    ("ex-strings-vowels", "s = input().strip()\nprint(sum(1 for ch in s if ch in 'aeiou'))\n", False),
    ("ex-types-divmod", "a, b = map(int, input().split())\nprint(round(a / b), a % b)\n", False),
    ("ex-algo-sort", "n = int(input())\nprint(*sorted(set(map(int, input().split()))))\n", False),
    ("ex-loops-sum", "n = int(input())\nprint(sum(range(1, n)))\n", False),
]
