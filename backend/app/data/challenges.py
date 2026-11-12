"""Practice challenges and their test cases.

Tests marked hidden=False are shown to students as samples. Hidden tests never leave the server:
the API returns only pass/fail status for them. Every expected output here is checked by independent
reference solutions in tests/test_challenges.py, so a typo in the data fails the test suite.

All challenges read from stdin and write to stdout, in C, Python or Java.
"""
from __future__ import annotations

from dataclasses import dataclass

Difficulty = str  # "beginner" | "intermediate" | "advanced"


@dataclass(frozen=True)
class TestCase:
    __test__ = False  # not a pytest test class, despite the name
    input: str
    expected: str
    hidden: bool = False
    note: str = ""  # shown with samples only


@dataclass(frozen=True)
class Challenge:
    id: str
    title: str
    difficulty: Difficulty
    summary: str
    statement: str
    input_format: str
    output_format: str
    constraints: tuple[str, ...]
    tags: tuple[str, ...]
    kind: str  # input shape, used to pick the starter code
    tests: tuple[TestCase, ...]


def S(inp: str, out: str, note: str = "") -> TestCase:
    return TestCase(inp, out, False, note)


def H(inp: str, out: str) -> TestCase:
    return TestCase(inp, out, True)


_FIZZ_1_15 = ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]
_FIZZ_16_30 = ["16", "17", "Fizz", "19", "Buzz", "Fizz", "22", "23", "Fizz", "Buzz", "26", "Fizz", "28", "29", "FizzBuzz"]

_OPEN_50 = "\n".join(["S" + "." * 49] + ["." * 50] * 48 + ["." * 49 + "E"])

CHALLENGES: tuple[Challenge, ...] = (
    # ------------------------------------------------------------------ beginner
    Challenge(
        id="sum-of-two",
        title="Sum of Two Numbers",
        difficulty="beginner",
        summary="Read two integers and print their sum.",
        statement="Read two integers a and b and print a + b.",
        input_format="One line with two integers a and b, separated by a space.",
        output_format="One integer: a + b.",
        constraints=("-1,000,000 ≤ a, b ≤ 1,000,000",),
        tags=("input", "arithmetic"),
        kind="two_ints",
        tests=(
            S("3 4\n", "7"),
            S("-5 12\n", "7", "Negative numbers work the same way."),
            H("0 0\n", "0"),
            H("-1000000 -1000000\n", "-2000000"),
            H("999999 1\n", "1000000"),
            H("17 -17\n", "0"),
        ),
    ),
    Challenge(
        id="even-or-odd",
        title="Even or Odd",
        difficulty="beginner",
        summary="Decide whether an integer is even or odd.",
        statement="Read an integer n. Print Even if n is even and Odd if n is odd. Zero is even. n can be negative.",
        input_format="One line with an integer n.",
        output_format="The word Even or the word Odd.",
        constraints=("-1,000,000,000 ≤ n ≤ 1,000,000,000",),
        tags=("conditions", "modulo"),
        kind="one_int",
        tests=(
            S("4\n", "Even"),
            S("7\n", "Odd"),
            H("0\n", "Even"),
            H("-3\n", "Odd"),
            H("-8\n", "Even"),
            H("1000000000\n", "Even"),
            H("999999999\n", "Odd"),
        ),
    ),
    Challenge(
        id="fizzbuzz",
        title="FizzBuzz",
        difficulty="beginner",
        summary="Count from 1 to n, replacing some numbers with words.",
        statement=(
            "Print the numbers from 1 to n, one per line. For multiples of 3 print Fizz instead of the number, "
            "for multiples of 5 print Buzz, and for multiples of both 3 and 5 print FizzBuzz."
        ),
        input_format="One line with an integer n.",
        output_format="n lines, as described above.",
        constraints=("1 ≤ n ≤ 100",),
        tags=("loops", "conditions"),
        kind="one_int",
        tests=(
            S("5\n", "1\n2\nFizz\n4\nBuzz"),
            S("3\n", "1\n2\nFizz"),
            H("1\n", "1"),
            H("15\n", "\n".join(_FIZZ_1_15)),
            H("30\n", "\n".join(_FIZZ_1_15 + _FIZZ_16_30)),
        ),
    ),
    # -------------------------------------------------------------- intermediate
    Challenge(
        id="palindrome-check",
        title="Palindrome Check",
        difficulty="intermediate",
        summary="Check whether a word reads the same forwards and backwards.",
        statement="Read a word made of lowercase letters. Print Yes if it is a palindrome and No if it is not.",
        input_format="One line with a single word s.",
        output_format="Yes or No.",
        constraints=("1 ≤ length of s ≤ 1,000", "s contains only the letters a to z"),
        tags=("strings", "two pointers"),
        kind="word",
        tests=(
            S("level\n", "Yes"),
            S("coding\n", "No"),
            H("a\n", "Yes"),
            H("abba\n", "Yes"),
            H("abca\n", "No"),
            H("racecar\n", "Yes"),
            H("ab\n", "No"),
            H("a" * 500 + "b" + "a" * 500 + "\n", "Yes"),
            H("a" * 500 + "bc" + "a" * 500 + "\n", "No"),
        ),
    ),
    Challenge(
        id="second-largest",
        title="Second Largest Number",
        difficulty="intermediate",
        summary="Find the second largest distinct value in a list.",
        statement=(
            "Given a list of integers, print the second largest distinct value. Equal numbers count once, "
            "so in 7 7 3 the second largest is 3. The list always contains at least two different values."
        ),
        input_format="The first line has n. The second line has n integers separated by spaces.",
        output_format="One integer.",
        constraints=("2 ≤ n ≤ 1,000", "-1,000,000,000 ≤ each number ≤ 1,000,000,000"),
        tags=("arrays", "sorting"),
        kind="int_list",
        tests=(
            S("5\n3 1 4 1 5\n", "4"),
            S("4\n7 7 3 3\n", "3", "Equal values count once."),
            H("2\n1 2\n", "1"),
            H("3\n-5 -1 -3\n", "-3"),
            H("6\n10 10 10 9 10 10\n", "9"),
            H("5\n1 2 3 4 5\n", "4"),
            H("4\n5 4 3 2\n", "4"),
            H("3\n-1000000000 1000000000 -1000000000\n", "-1000000000"),
        ),
    ),
    Challenge(
        id="prime-count",
        title="Counting Primes",
        difficulty="intermediate",
        summary="Count the prime numbers up to n.",
        statement=(
            "A prime is a number greater than 1 whose only divisors are 1 and itself. "
            "Print how many primes are less than or equal to n."
        ),
        input_format="One line with an integer n.",
        output_format="One integer.",
        constraints=("1 ≤ n ≤ 100,000",),
        tags=("math", "loops", "sieve"),
        kind="one_int",
        tests=(
            S("10\n", "4", "The primes up to 10 are 2, 3, 5 and 7."),
            S("30\n", "10"),
            H("1\n", "0"),
            H("2\n", "1"),
            H("97\n", "25"),
            H("100\n", "25"),
            H("1000\n", "168"),
            H("100000\n", "9592"),
        ),
    ),
    # ----------------------------------------------------------------- advanced
    Challenge(
        id="balanced-brackets",
        title="Balanced Brackets",
        difficulty="advanced",
        summary="Check that every bracket is closed in the right order.",
        statement=(
            "A string of the brackets ( ) [ ] { } is balanced when every opening bracket is closed by the same "
            "kind of bracket, and brackets close in the reverse order they opened. Print Balanced or Not balanced."
        ),
        input_format="One line with a string s of brackets, no spaces.",
        output_format="Balanced or Not balanced.",
        constraints=("1 ≤ length of s ≤ 100,000",),
        tags=("stack", "strings"),
        kind="word",
        tests=(
            S("([]{})\n", "Balanced"),
            S("([)]\n", "Not balanced", "The ) closes before the [ does."),
            H("(\n", "Not balanced"),
            H(")\n", "Not balanced"),
            H("()[]{}\n", "Balanced"),
            H("{[()]}\n", "Balanced"),
            H("(((\n", "Not balanced"),
            H("(()\n", "Not balanced"),
            H("())(\n", "Not balanced"),
            H("][\n", "Not balanced"),
            H("[" * 50000 + "]" * 50000 + "\n", "Balanced"),
            H("[" * 50000 + "]" * 49999 + "\n", "Not balanced"),
        ),
    ),
    Challenge(
        id="longest-increasing-subsequence",
        title="Longest Increasing Subsequence",
        difficulty="advanced",
        summary="Find the length of the longest strictly increasing subsequence.",
        statement=(
            "A subsequence keeps the original order but may skip numbers. Given a list of integers, print the length "
            "of the longest subsequence whose values are strictly increasing."
        ),
        input_format="The first line has n. The second line has n integers separated by spaces.",
        output_format="One integer.",
        constraints=("1 ≤ n ≤ 2,000", "-1,000,000 ≤ each number ≤ 1,000,000"),
        tags=("dynamic programming", "arrays"),
        kind="int_list",
        tests=(
            S("8\n10 9 2 5 3 7 101 18\n", "4", "One longest choice is 2, 3, 7, 18."),
            S("4\n7 7 7 7\n", "1", "Strictly increasing, so equal numbers do not extend it."),
            H("1\n5\n", "1"),
            H("5\n1 2 3 4 5\n", "5"),
            H("5\n5 4 3 2 1\n", "1"),
            H("10\n1 3 2 4 3 5 4 6 5 7\n", "6"),
            H("1000\n" + " ".join(map(str, range(1, 1001))) + "\n", "1000"),
            H("1000\n" + " ".join(map(str, range(1000, 0, -1))) + "\n", "1"),
        ),
    ),
    Challenge(
        id="shortest-path-grid",
        title="Shortest Path in a Grid",
        difficulty="advanced",
        summary="Find the fewest steps from S to E, walking around walls.",
        statement=(
            "A grid has open cells (.), walls (#), a start S and an exit E. In one step you can move to the cell "
            "above, below, left or right, never onto a wall or outside the grid. "
            "Print the smallest number of steps from S to E, or -1 if E cannot be reached."
        ),
        input_format="The first line has R and C. The next R lines each have C characters from . # S E.",
        output_format="One integer: the minimum number of steps, or -1.",
        constraints=("1 ≤ R, C ≤ 100", "The grid has exactly one S and one E"),
        tags=("graphs", "BFS", "queue"),
        kind="grid",
        tests=(
            S("3 4\nS..#\n.#..\n...E\n", "5"),
            S("2 3\nS#E\n.#.\n", "-1", "A column of walls blocks every route."),
            H("1 2\nSE\n", "1"),
            H("1 3\nS#E\n", "-1"),
            H("3 3\nS..\n...\n..E\n", "4"),
            H("3 3\nS.#\n##.\n..E\n", "-1"),
            H("4 4\nS#..\n.#.#\n.#.E\n...#\n", "7"),
            H("3 3\n.#.\n#S#\n.#E\n", "-1"),
            H("50 50\n" + _OPEN_50 + "\n", "98"),
        ),
    ),
)

BY_ID: dict[str, Challenge] = {c.id: c for c in CHALLENGES}

# --------------------------------------------------------------------------- starter code
# One starter per input shape and language. Each reads the input for you, prints a placeholder answer,
# and leaves the real work to the student.
STARTERS: dict[str, dict[str, str]] = {
    "one_int": {
        "python": 'n = int(input())\n\n# Write your solution here, then print the answer.\nprint(0)\n',
        "c": '#include <stdio.h>\n\nint main(void) {\n    int n;\n    scanf("%d", &n);\n\n    /* Write your solution here, then print the answer. */\n    printf("%d\\n", 0);\n    return 0;\n}\n',
        "java": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        int n = in.nextInt();\n\n        // Write your solution here, then print the answer.\n        System.out.println(0);\n    }\n}\n',
    },
    "two_ints": {
        "python": 'a, b = map(int, input().split())\n\n# Write your solution here, then print the answer.\nprint(0)\n',
        "c": '#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    scanf("%d %d", &a, &b);\n\n    /* Write your solution here, then print the answer. */\n    printf("%d\\n", 0);\n    return 0;\n}\n',
        "java": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        int a = in.nextInt();\n        int b = in.nextInt();\n\n        // Write your solution here, then print the answer.\n        System.out.println(0);\n    }\n}\n',
    },
    "word": {
        "python": 's = input().strip()\n\n# Write your solution here, then print the answer.\nprint("No")\n',
        "c": '#include <stdio.h>\n#include <string.h>\n\nint main(void) {\n    static char s[100005];\n    scanf("%100000s", s);\n    int len = (int)strlen(s);\n\n    /* Write your solution here, then print the answer. */\n    (void)len;\n    printf("No\\n");\n    return 0;\n}\n',
        "java": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        String s = in.next();\n\n        // Write your solution here, then print the answer.\n        System.out.println("No");\n    }\n}\n',
    },
    "int_list": {
        "python": 'n = int(input())\nnums = list(map(int, input().split()))\n\n# Write your solution here, then print the answer.\nprint(0)\n',
        "c": '#include <stdio.h>\n\nint main(void) {\n    int n;\n    static int nums[2005];\n    scanf("%d", &n);\n    for (int i = 0; i < n; i++) {\n        scanf("%d", &nums[i]);\n    }\n\n    /* Write your solution here, then print the answer. */\n    printf("%d\\n", 0);\n    return 0;\n}\n',
        "java": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        int n = in.nextInt();\n        int[] nums = new int[n];\n        for (int i = 0; i < n; i++) {\n            nums[i] = in.nextInt();\n        }\n\n        // Write your solution here, then print the answer.\n        System.out.println(0);\n    }\n}\n',
    },
    "grid": {
        "python": 'r, c = map(int, input().split())\ngrid = [input().strip() for _ in range(r)]\n\n# Write your solution here, then print the answer.\nprint(-1)\n',
        "c": '#include <stdio.h>\n\nint main(void) {\n    int r, c;\n    static char grid[105][105];\n    scanf("%d %d", &r, &c);\n    for (int i = 0; i < r; i++) {\n        scanf("%104s", grid[i]);\n    }\n\n    /* Write your solution here, then print the answer. */\n    printf("%d\\n", -1);\n    return 0;\n}\n',
        "java": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        int r = in.nextInt();\n        int c = in.nextInt();\n        String[] grid = new String[r];\n        for (int i = 0; i < r; i++) {\n            grid[i] = in.next();\n        }\n\n        // Write your solution here, then print the answer.\n        System.out.println(-1);\n    }\n}\n',
    },
}
