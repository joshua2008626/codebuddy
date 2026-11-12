"""Learning Hub content: 12 lessons, each with explanations, runnable examples and one graded exercise.

Every example lists the output it prints. tests/test_lessons.py runs each one through real compilers and
checks that output, so a lesson can never show output the code does not produce. Exercises are ordinary
challenges (same grader, same hidden-test rules) that are kept out of the practice list.
"""
from __future__ import annotations

from dataclasses import dataclass

from .challenges import Challenge, H, S


@dataclass(frozen=True)
class Example:
    title: str
    language: str  # "python" | "c" | "java"
    code: str
    output: str  # exactly what the program prints (trailing newline omitted)
    stdin: str = ""


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    group: str  # "Languages" | "Core concepts" | "Going further"
    summary: str
    minutes: int
    sections: tuple[tuple[str, str], ...]  # (heading, markdown body)
    examples: tuple[Example, ...]
    exercise_id: str


def _ex(title: str, language: str, code: str, output: str, stdin: str = "") -> Example:
    return Example(title, language, code.strip("\n") + "\n", output, stdin)


def _trio(title: str, py: str, c: str, java: str, output: str) -> tuple[Example, ...]:
    return (_ex(title, "python", py, output), _ex(title, "c", c, output), _ex(title, "java", java, output))


# ===================================================================================== exercises
EXERCISES: tuple[Challenge, ...] = (
    Challenge(
        id="ex-c-product", title="Multiply", difficulty="beginner",
        summary="Read two integers and print their product.",
        statement="Read two integers a and b and print a × b.",
        input_format="One line with two integers a and b, separated by a space.",
        output_format="One integer.",
        constraints=("-30000 ≤ a, b ≤ 30000",), tags=("c", "input", "arithmetic"), kind="two_ints",
        tests=(S("3 4", "12"), S("-2 5", "-10", "A negative number works the same way."),
               H("0 9", "0"), H("-7 -6", "42"), H("30000 30000", "900000000")),
    ),
    Challenge(
        id="ex-py-echo", title="Say It Twice", difficulty="beginner",
        summary="Read a word and print it twice on one line.",
        statement="Read one word and print it two times, separated by a single space.",
        input_format="One word with no spaces.", output_format="The word, a space, then the word again.",
        constraints=("1 ≤ length ≤ 100",), tags=("python", "strings", "output"), kind="word",
        tests=(S("hello", "hello hello"), S("Py", "Py Py"), H("a", "a a"), H("codebuddy", "codebuddy codebuddy"), H("X1", "X1 X1")),
    ),
    Challenge(
        id="ex-java-square", title="Square a Number", difficulty="beginner",
        summary="Read an integer and print its square.",
        statement="Read an integer n and print n × n.",
        input_format="One integer n.", output_format="One integer.",
        constraints=("-40000 ≤ n ≤ 40000", "The answer always fits in a 32-bit int."), tags=("java", "arithmetic"), kind="one_int",
        tests=(S("5", "25"), S("-3", "9", "The square of a negative number is positive."),
               H("0", "0"), H("40000", "1600000000"), H("-40000", "1600000000")),
    ),
    Challenge(
        id="ex-types-divmod", title="Quotient and Remainder", difficulty="beginner",
        summary="Divide two integers and print the whole-number quotient and the remainder.",
        statement="Read positive integers a and b. Print the integer quotient of a ÷ b (no decimals) and the remainder, separated by a space.",
        input_format="One line with a and b.", output_format="Two integers: quotient and remainder.",
        constraints=("1 ≤ a ≤ 1000000", "1 ≤ b ≤ 1000000"), tags=("types", "arithmetic"), kind="two_ints",
        tests=(S("7 2", "3 1", "7 = 3 × 2 + 1"), S("20 5", "4 0"),
               H("1 9", "0 1"), H("100 7", "14 2"), H("1000000 3", "333333 1")),
    ),
    Challenge(
        id="ex-conditionals-sign", title="Positive, Negative or Zero", difficulty="beginner",
        summary="Classify an integer.",
        statement="Read an integer n. Print Positive if n > 0, Negative if n < 0, and Zero if n is 0.",
        input_format="One integer n.", output_format="Exactly one of: Positive, Negative, Zero.",
        constraints=("-1000000000 ≤ n ≤ 1000000000",), tags=("conditionals",), kind="one_int",
        tests=(S("5", "Positive"), S("-2", "Negative"), H("0", "Zero"), H("1", "Positive"), H("-1000000000", "Negative")),
    ),
    Challenge(
        id="ex-loops-sum", title="Sum from 1 to n", difficulty="beginner",
        summary="Add up the numbers 1 through n.",
        statement="Read n and print 1 + 2 + … + n.",
        input_format="One integer n.", output_format="One integer.",
        constraints=("1 ≤ n ≤ 60000", "The answer fits in a 32-bit int."), tags=("loops",), kind="one_int",
        tests=(S("5", "15", "1 + 2 + 3 + 4 + 5"), S("10", "55"), H("1", "1"), H("100", "5050"), H("60000", "1800030000")),
    ),
    Challenge(
        id="ex-functions-factorial", title="Factorial", difficulty="beginner",
        summary="Write a function that returns n!.",
        statement="Read n and print n! (n factorial: 1 × 2 × … × n, and 0! = 1). Put the calculation in a function of your own.",
        input_format="One integer n.", output_format="One integer.",
        constraints=("0 ≤ n ≤ 12",), tags=("functions", "recursion"), kind="one_int",
        tests=(S("5", "120"), S("0", "1", "By definition, 0! is 1."), H("1", "1"), H("10", "3628800"), H("12", "479001600")),
    ),
    Challenge(
        id="ex-arrays-max", title="Largest Element", difficulty="beginner",
        summary="Find the biggest number in an array.",
        statement="Read n integers and print the largest one. Loop through the array once, remembering the best value so far.",
        input_format="The first line has n. The second line has n integers.", output_format="One integer.",
        constraints=("1 ≤ n ≤ 2000", "-10^9 ≤ each value ≤ 10^9"), tags=("arrays",), kind="int_list",
        tests=(S("5\n3 9 2 7 1", "9"), S("3\n-5 -2 -9", "-2", "With only negative numbers, start from the first element, not 0."),
               H("1\n42", "42"), H("4\n-1000000000 -1000000000 -1000000000 -999999999", "-999999999"), H("6\n5 5 5 5 5 5", "5")),
    ),
    Challenge(
        id="ex-strings-vowels", title="Count the Vowels", difficulty="beginner",
        summary="Count a, e, i, o, u in a word, ignoring case.",
        statement="Read one word and print how many of its letters are vowels (a, e, i, o, u, in upper or lower case).",
        input_format="One word of letters.", output_format="One integer.",
        constraints=("1 ≤ length ≤ 100",), tags=("strings",), kind="word",
        tests=(S("hello", "2"), S("rhythm", "0", "No vowels at all."), H("AEIOU", "5"), H("Programming", "3"), H("a", "1")),
    ),
    Challenge(
        id="ex-ds-first-unique", title="First Unique Character", difficulty="intermediate",
        summary="Use a frequency table to find the first character that appears only once.",
        statement="Read a word. Print the first character (from the left) that appears exactly once in the word, or none if every character repeats.",
        input_format="One word of lowercase letters.", output_format="One character, or the word none.",
        constraints=("1 ≤ length ≤ 100",), tags=("data structures", "hash map"), kind="word",
        tests=(S("swiss", "w", "s repeats; w is the first letter that does not."), S("aabb", "none"),
               H("z", "z"), H("abcabcd", "d"), H("level", "v"), H("mississippi", "m"), H("hello", "h")),
    ),
    Challenge(
        id="ex-algo-sort", title="Sort the Numbers", difficulty="intermediate",
        summary="Sort an array without calling a library sort.",
        statement="Read n integers and print them in ascending order, separated by spaces. Write the sorting loop yourself (for example selection sort or bubble sort).",
        input_format="The first line has n. The second line has n integers.", output_format="The n integers in ascending order on one line.",
        constraints=("1 ≤ n ≤ 2000", "-10^9 ≤ each value ≤ 10^9"), tags=("algorithms", "sorting"), kind="int_list",
        tests=(S("5\n4 2 5 1 3", "1 2 3 4 5"), S("3\n9 9 -1", "-1 9 9", "Duplicates stay."),
               H("1\n7", "7"), H("6\n3 1 2 3 1 2", "1 1 2 2 3 3"), H("4\n10 -10 0 5", "-10 0 5 10"), H("5\n1 2 3 4 5", "1 2 3 4 5")),
    ),
    Challenge(
        id="ex-oop-rectangle", title="Rectangle Class", difficulty="intermediate",
        summary="Model a rectangle as a class (or struct) with an area and a perimeter.",
        statement="Read a width and a height. Create a Rectangle (a class in Python or Java, a struct plus functions in C) and print its area and its perimeter, separated by a space.",
        input_format="One line with width and height.", output_format="Two integers: area and perimeter.",
        constraints=("1 ≤ width, height ≤ 10000",), tags=("oop",), kind="two_ints",
        tests=(S("3 4", "12 14"), S("5 5", "25 20", "A square is a rectangle."), H("1 1", "1 4"), H("10000 10000", "100000000 40000"), H("7 2", "14 18")),
    ),
)

EXERCISE_BY_ID: dict[str, Challenge] = {c.id: c for c in EXERCISES}

# ======================================================================================== lessons
LESSONS: tuple[Lesson, ...] = (
    # ------------------------------------------------------------------------------- languages
    Lesson(
        id="c-fundamentals", title="C fundamentals", group="Languages", minutes=12,
        summary="The shape of a C program: headers, main, printf and scanf.",
        sections=(
            ("How a C program is built",
             "C is a **compiled** language: a compiler turns your source file into a program before it runs. Every program starts at a function called `main`, and returns `0` to say it finished normally.\n\n"
             "Lines starting with `#include` pull in libraries. `<stdio.h>` gives you `printf` (output) and `scanf` (input)."),
            ("Printing and reading",
             "- `printf(\"%d\\n\", n)` prints an integer, then a new line. `%d` is for `int`, `%f` for `double`, `%s` for text, `%c` for one character.\n"
             "- `scanf(\"%d\", &n)` reads an integer into `n`. The `&` passes the variable's address so `scanf` can change it.\n"
             "- Every statement ends with a semicolon, and blocks use `{ }`."),
            ("Things that trip people up",
             "- C does not check array bounds. Reading past the end is undefined behaviour, not an error message.\n"
             "- `int` has a fixed size (usually 32 bits), so very large results overflow silently.\n"
             "- Text is an array of `char` ending in a `'\\0'` byte."),
        ),
        examples=(
            _ex("A first program", "c", """
#include <stdio.h>

int main(void) {
    int apples = 3;
    printf("I have %d apples\\n", apples);
    return 0;
}
""", "I have 3 apples"),
            _ex("Reading input", "c", """
#include <stdio.h>

int main(void) {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}
""", "9", stdin="4 5\n"),
        ),
        exercise_id="ex-c-product",
    ),
    Lesson(
        id="python-fundamentals", title="Python fundamentals", group="Languages", minutes=12,
        summary="Python's clean syntax: print, input, indentation and comprehensions.",
        sections=(
            ("Readable by design",
             "Python is **interpreted** and uses indentation to group code, so there are no braces. A statement ends at the end of the line. Variables are created by assigning to them and need no declared type."),
            ("Input and output",
             "- `print(a, b)` prints values separated by a space.\n"
             "- `input()` reads one line as text. Convert it with `int(...)` or `float(...)`.\n"
             "- `a, b = map(int, input().split())` reads two numbers from one line.\n"
             "- f-strings insert values into text: `f\"{name} is {age}\"`."),
            ("Built-in tools",
             "Lists (`[1, 2, 3]`), dictionaries (`{\"a\": 1}`) and strings come with many methods. A **list comprehension** such as `[n * n for n in range(1, 6)]` builds a list in one line.\n\n"
             "Python integers never overflow, but loops are slower than in C or Java."),
        ),
        examples=(
            _ex("Strings and f-strings", "python", """
name = "Ada"
age = 36
print(f"{name} is {age}")
print(name.upper(), len(name))
""", "Ada is 36\nADA 3"),
            _ex("A list comprehension", "python", """
squares = [n * n for n in range(1, 6)]
print(squares)
print(sum(squares))
""", "[1, 4, 9, 16, 25]\n55"),
        ),
        exercise_id="ex-py-echo",
    ),
    Lesson(
        id="java-fundamentals", title="Java fundamentals", group="Languages", minutes=12,
        summary="Classes, static main, System.out and Scanner.",
        sections=(
            ("Everything lives in a class",
             "Java is **compiled** (to bytecode run by the JVM) and **statically typed**: every variable has a declared type. A program starts at `public static void main(String[] args)` inside a class. On CodeBuddy the class is called `Main`."),
            ("Input and output",
             "- `System.out.println(x)` prints and ends the line; `System.out.print(x)` does not end it.\n"
             "- `String.format(\"%.2f\", x)` (or `System.out.printf`) formats numbers.\n"
             "- `Scanner in = new Scanner(System.in);` then `in.nextInt()`, `in.next()` (a word) or `in.nextLine()` (a line)."),
            ("Types to know",
             "Primitives: `int`, `long`, `double`, `boolean`, `char`. Objects such as `String` and `ArrayList` start with a capital letter. Compare strings with `.equals(...)`, never `==`."),
        ),
        examples=(
            _ex("A first program", "java", """
public class Main {
    public static void main(String[] args) {
        int apples = 3;
        System.out.println("I have " + apples + " apples");
        System.out.println(String.format("%.2f", 2.0 / 3));
    }
}
""", "I have 3 apples\n0.67"),
            _ex("Reading input", "java", """
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        int a = in.nextInt();
        int b = in.nextInt();
        System.out.println(a + b);
    }
}
""", "9", stdin="4 5\n"),
        ),
        exercise_id="ex-java-square",
    ),
    # --------------------------------------------------------------------------- core concepts
    Lesson(
        id="variables-types", title="Variables and data types", group="Core concepts", minutes=10,
        summary="Integers, decimals, text, and why 7 / 2 is not always 3.5.",
        sections=(
            ("Variables",
             "A variable is a named place that holds a value. Choose names that say what the value means (`total`, not `t`)."),
            ("The basic types",
             "- **Integers** (`int`) are whole numbers.\n- **Decimals** (`double` in C and Java, `float` in Python) hold fractional numbers, with tiny rounding errors.\n- **Text** (`String`, `str`, or a `char` array in C).\n- **Booleans** are true or false (`bool` in Python, `boolean` in Java, `int` 0/1 in classic C)."),
            ("Division and overflow",
             "In C and Java, dividing two integers gives an integer: `7 / 2` is `3`, and `7 % 2` (the remainder) is `1`. Convert one side to `double` to get `3.5`.\n\n"
             "Python has two operators: `/` always gives a decimal and `//` divides whole numbers.\n\n"
             "A C or Java `int` is 32 bits and wraps around past about 2.1 billion. Use `long` when numbers may be that large."),
        ),
        examples=_trio("Integer and decimal division", """
a = 7
b = 2
print(a // b)
print(a % b)
print(a / b)
name = "Ada"
print(name, len(name))
""", """
#include <stdio.h>
#include <string.h>

int main(void) {
    int a = 7, b = 2;
    printf("%d\\n", a / b);
    printf("%d\\n", a % b);
    printf("%.1f\\n", (double)a / b);
    char name[] = "Ada";
    printf("%s %d\\n", name, (int)strlen(name));
    return 0;
}
""", """
public class Main {
    public static void main(String[] args) {
        int a = 7, b = 2;
        System.out.println(a / b);
        System.out.println(a % b);
        System.out.println((double) a / b);
        String name = "Ada";
        System.out.println(name + " " + name.length());
    }
}
""", "3\n1\n3.5\nAda 3"),
        exercise_id="ex-types-divmod",
    ),
    Lesson(
        id="conditionals", title="Conditional statements", group="Core concepts", minutes=10,
        summary="if, else if and else: making decisions.",
        sections=(
            ("Choosing a path",
             "A conditional runs code only when a test is true. The test is a **boolean expression** such as `score >= 70` or `n % 2 == 0`. Conditions are checked top to bottom and the first true branch wins."),
            ("Building tests",
             "- Comparisons: `==` equal, `!=` not equal, `<`, `<=`, `>`, `>=`.\n- Combine with `and` / `or` / `not` in Python, and `&&` / `||` / `!` in C and Java.\n- A single `=` assigns; `==` compares. Mixing them up is a classic bug."),
            ("Order matters",
             "Put the most specific test first. In a grading chain, check `>= 90` before `>= 70`, otherwise a 95 would match the wrong branch."),
        ),
        examples=_trio("Grade and parity", """
score = 72
if score >= 90:
    print("A")
elif score >= 70:
    print("B")
else:
    print("C")
print("even" if score % 2 == 0 else "odd")
""", """
#include <stdio.h>

int main(void) {
    int score = 72;
    if (score >= 90) {
        printf("A\\n");
    } else if (score >= 70) {
        printf("B\\n");
    } else {
        printf("C\\n");
    }
    printf("%s\\n", score % 2 == 0 ? "even" : "odd");
    return 0;
}
""", """
public class Main {
    public static void main(String[] args) {
        int score = 72;
        if (score >= 90) {
            System.out.println("A");
        } else if (score >= 70) {
            System.out.println("B");
        } else {
            System.out.println("C");
        }
        System.out.println(score % 2 == 0 ? "even" : "odd");
    }
}
""", "B\neven"),
        exercise_id="ex-conditionals-sign",
    ),
    Lesson(
        id="loops", title="Loops", group="Core concepts", minutes=10,
        summary="for and while: repeating work without repeating code.",
        sections=(
            ("Two kinds of loop",
             "- A **for** loop repeats a known number of times, or once per item in a collection.\n- A **while** loop repeats as long as a condition stays true. Make sure something inside the loop eventually makes it false, or it never ends."),
            ("Accumulators",
             "Many loops build up an answer: start a variable before the loop (`total = 0`), update it each pass (`total += i`), and use it afterwards."),
            ("Off-by-one errors",
             "Ranges usually include the start and exclude the end: Python's `range(1, 6)` gives 1 to 5. Check the first and last pass by hand when something is one too many or too few."),
        ),
        examples=_trio("Sum and countdown", """
total = 0
for i in range(1, 6):
    total += i
print(total)
n = 3
while n > 0:
    print(n)
    n -= 1
print("go")
""", """
#include <stdio.h>

int main(void) {
    int total = 0;
    for (int i = 1; i <= 5; i++) {
        total += i;
    }
    printf("%d\\n", total);
    int n = 3;
    while (n > 0) {
        printf("%d\\n", n);
        n--;
    }
    printf("go\\n");
    return 0;
}
""", """
public class Main {
    public static void main(String[] args) {
        int total = 0;
        for (int i = 1; i <= 5; i++) {
            total += i;
        }
        System.out.println(total);
        int n = 3;
        while (n > 0) {
            System.out.println(n);
            n--;
        }
        System.out.println("go");
    }
}
""", "15\n3\n2\n1\ngo"),
        exercise_id="ex-loops-sum",
    ),
    Lesson(
        id="functions", title="Functions", group="Core concepts", minutes=10,
        summary="Name a piece of work, give it inputs, get a result back.",
        sections=(
            ("Why functions",
             "A function packages a task under a name. You write it once and call it many times. It takes **parameters** (inputs) and may **return** a value."),
            ("Parts of a function",
             "- A name that says what it does (`area`, `greet`).\n- Parameters, which are local to the function.\n- A `return` statement. In C and Java, a function that returns nothing is declared `void`; in Python it simply has no `return`."),
            ("Recursion",
             "A function can call itself. It needs a **base case** that stops the calls, and each call must move closer to it. For example `factorial(n) = n * factorial(n - 1)`, with `factorial(0) = 1`."),
        ),
        examples=_trio("Two small functions", """
def area(w, h):
    return w * h


def greet(name):
    print("Hello, " + name)


greet("Ada")
print(area(3, 4))
""", """
#include <stdio.h>

int area(int w, int h) {
    return w * h;
}

void greet(const char *name) {
    printf("Hello, %s\\n", name);
}

int main(void) {
    greet("Ada");
    printf("%d\\n", area(3, 4));
    return 0;
}
""", """
public class Main {
    static int area(int w, int h) {
        return w * h;
    }

    static void greet(String name) {
        System.out.println("Hello, " + name);
    }

    public static void main(String[] args) {
        greet("Ada");
        System.out.println(area(3, 4));
    }
}
""", "Hello, Ada\n12"),
        exercise_id="ex-functions-factorial",
    ),
    Lesson(
        id="arrays", title="Arrays", group="Core concepts", minutes=10,
        summary="Storing many values in order and reaching them by index.",
        sections=(
            ("A row of boxes",
             "An array holds several values of the same kind, numbered from **0**. The first item is `nums[0]` and the last of four is `nums[3]`."),
            ("Arrays across languages",
             "- **C**: a fixed size, chosen when you declare it (`int nums[4]`). No bounds checking, and the array does not remember its own length.\n- **Java**: fixed size too, but `nums.length` is always available and bad indexes throw an exception.\n- **Python**: lists grow and shrink (`append`, `pop`), and negative indexes count from the end (`nums[-1]`)."),
            ("Walking through an array",
             "Use a loop over the indexes (or the items) to add up, search or compare. To find a maximum, start with the first element and replace it whenever you see something larger."),
        ),
        examples=_trio("Indexing and totals", """
nums = [5, 3, 8]
nums.append(1)
print(nums[0], nums[-1], len(nums))
total = 0
for x in nums:
    total += x
print(total)
""", """
#include <stdio.h>

int main(void) {
    int nums[4] = {5, 3, 8, 1};
    int len = (int)(sizeof nums / sizeof nums[0]);
    printf("%d %d %d\\n", nums[0], nums[len - 1], len);
    int total = 0;
    for (int i = 0; i < len; i++) {
        total += nums[i];
    }
    printf("%d\\n", total);
    return 0;
}
""", """
public class Main {
    public static void main(String[] args) {
        int[] nums = {5, 3, 8, 1};
        System.out.println(nums[0] + " " + nums[nums.length - 1] + " " + nums.length);
        int total = 0;
        for (int x : nums) {
            total += x;
        }
        System.out.println(total);
    }
}
""", "5 1 4\n17"),
        exercise_id="ex-arrays-max",
    ),
    Lesson(
        id="strings", title="Strings", group="Core concepts", minutes=10,
        summary="Text as a sequence of characters: count, reverse, change case.",
        sections=(
            ("Text is a sequence",
             "A string is an ordered list of characters, so you can loop over it and index it just like an array. Strings in Python and Java are **immutable**: operations return a new string instead of changing the old one."),
            ("Common jobs",
             "- Length: `len(s)`, `s.length()`, `strlen(s)`.\n- Case: `s.upper()`, `s.toUpperCase()`, `toupper(ch)` in C.\n- Comparing: Python `==`, Java `.equals()`, C `strcmp()`. Never use `==` on Java strings or C `char` arrays.\n- Searching and replacing: `find` / `indexOf` / `strstr`."),
            ("In C, a string is an array",
             "A C string is a `char` array that ends with a zero byte `'\\0'`. `strlen` counts up to that byte, so the array must be one byte bigger than the text."),
        ),
        examples=_trio("Count, reverse, upper-case", """
s = "hello world"
count = 0
for ch in s:
    if ch == "l":
        count += 1
print(count)
print(s[::-1])
print(s.upper())
""", """
#include <ctype.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    char s[] = "hello world";
    int len = (int)strlen(s), count = 0;
    for (int i = 0; i < len; i++) {
        if (s[i] == 'l') count++;
    }
    printf("%d\\n", count);
    for (int i = len - 1; i >= 0; i--) putchar(s[i]);
    putchar('\\n');
    for (int i = 0; i < len; i++) putchar(toupper((unsigned char)s[i]));
    putchar('\\n');
    return 0;
}
""", """
public class Main {
    public static void main(String[] args) {
        String s = "hello world";
        int count = 0;
        for (char ch : s.toCharArray()) {
            if (ch == 'l') count++;
        }
        System.out.println(count);
        System.out.println(new StringBuilder(s).reverse());
        System.out.println(s.toUpperCase());
    }
}
""", "3\ndlrow olleh\nHELLO WORLD"),
        exercise_id="ex-strings-vowels",
    ),
    # -------------------------------------------------------------------------- going further
    Lesson(
        id="data-structures", title="Data structures", group="Going further", minutes=14,
        summary="Stacks and hash maps: the right container makes the problem easy.",
        sections=(
            ("Choosing a container",
             "A data structure is a way of organising data so the operations you need are fast and simple. Two everyday ones:"),
            ("Stack: last in, first out",
             "You can only add (`push`) and remove (`pop`) at the top, like a pile of plates. Stacks undo actions, evaluate expressions and match brackets. Python uses a list (`append`/`pop`), Java uses `ArrayDeque`, and in C you can use an array plus a `top` counter."),
            ("Hash map: look up by key",
             "A hash map (a `dict` in Python, `HashMap` in Java) stores key → value pairs and finds a key in roughly constant time. A common use is a **frequency table**: map each character to how many times it appears.\n\n"
             "In C there is no built-in map, but when keys are characters you can use an array of 256 counters indexed by the character."),
        ),
        examples=_trio("A stack and a frequency table", """
stack = []
stack.append("a")
stack.append("b")
print(stack.pop())
counts = {}
for ch in "banana":
    counts[ch] = counts.get(ch, 0) + 1
print(counts["a"], counts["n"], counts["b"])
""", """
#include <stdio.h>

int main(void) {
    char stack[10];
    int top = 0;
    stack[top++] = 'a';
    stack[top++] = 'b';
    printf("%c\\n", stack[--top]);
    int counts[256] = {0};
    const char *s = "banana";
    for (int i = 0; s[i] != '\\0'; i++) counts[(unsigned char)s[i]]++;
    printf("%d %d %d\\n", counts['a'], counts['n'], counts['b']);
    return 0;
}
""", """
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        Deque<String> stack = new ArrayDeque<>();
        stack.push("a");
        stack.push("b");
        System.out.println(stack.pop());
        Map<Character, Integer> counts = new HashMap<>();
        for (char ch : "banana".toCharArray()) {
            counts.put(ch, counts.getOrDefault(ch, 0) + 1);
        }
        System.out.println(counts.get('a') + " " + counts.get('n') + " " + counts.get('b'));
    }
}
""", "b\n3 2 1"),
        exercise_id="ex-ds-first-unique",
    ),
    Lesson(
        id="algorithms", title="Algorithms", group="Going further", minutes=14,
        summary="Binary search, sorting, and how to compare approaches.",
        sections=(
            ("What an algorithm is",
             "An algorithm is a precise step-by-step method for solving a problem. Two correct algorithms can differ hugely in speed, which is described with **Big-O**: how the work grows as the input grows."),
            ("Searching",
             "- **Linear search** checks every item: O(n).\n- **Binary search** works on a *sorted* array. Look at the middle: if it is too small, discard the left half, otherwise the right half. Each step halves the range, so it takes O(log n) steps. A million items need about 20 checks."),
            ("Sorting",
             "Simple sorts such as **selection sort** (repeatedly move the smallest remaining item to the front) and **bubble sort** take O(n²) time. They are easy to write and fine for small inputs. Library sorts use faster methods, typically O(n log n)."),
        ),
        examples=_trio("Binary search", """
def binary_search(items, target):
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


data = [1, 3, 5, 7, 9]
print(binary_search(data, 7))
print(binary_search(data, 4))
""", """
#include <stdio.h>

int binary_search(const int *items, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (items[mid] == target) return mid;
        if (items[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

int main(void) {
    int data[] = {1, 3, 5, 7, 9};
    printf("%d\\n", binary_search(data, 5, 7));
    printf("%d\\n", binary_search(data, 5, 4));
    return 0;
}
""", """
public class Main {
    static int binarySearch(int[] items, int target) {
        int lo = 0, hi = items.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (items[mid] == target) return mid;
            if (items[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    public static void main(String[] args) {
        int[] data = {1, 3, 5, 7, 9};
        System.out.println(binarySearch(data, 7));
        System.out.println(binarySearch(data, 4));
    }
}
""", "3\n-1"),
        exercise_id="ex-algo-sort",
    ),
    Lesson(
        id="oop", title="Object-oriented programming", group="Going further", minutes=14,
        summary="Classes, objects, and inheritance (and how C approximates them).",
        sections=(
            ("Objects bundle data and behaviour",
             "A **class** is a blueprint. An **object** is one thing built from it. A `Rectangle` class holds a `width` and `height` (its data) and an `area()` method (its behaviour)."),
            ("Core ideas",
             "- **Encapsulation**: keep data and the code that uses it together, and hide details callers do not need.\n- **Inheritance**: a class can extend another and reuse it. A `Square` is a `Rectangle` with equal sides.\n- **Polymorphism**: code can work with a `Rectangle` and not care whether it is really a `Square`."),
            ("Language notes",
             "Python and Java have classes. **C has no classes**, but the same idea works with a `struct` for the data and functions that take it as an argument, so the C example below is object-style rather than true OOP and has no inheritance."),
        ),
        examples=(
            _ex("A class and a subclass", "python", """
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height


class Square(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)


print(Rectangle(3, 4).area())
print(Square(5).area())
""", "12\n25"),
            _ex("A struct and functions", "c", """
#include <stdio.h>

struct Rectangle {
    int width;
    int height;
};

int area(struct Rectangle r) {
    return r.width * r.height;
}

int main(void) {
    struct Rectangle r = {3, 4};
    struct Rectangle square = {5, 5};
    printf("%d\\n", area(r));
    printf("%d\\n", area(square));
    return 0;
}
""", "12\n25"),
            _ex("A class and a subclass", "java", """
class Rectangle {
    protected final int width;
    protected final int height;

    Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }

    int area() {
        return width * height;
    }
}

class Square extends Rectangle {
    Square(int side) {
        super(side, side);
    }
}

public class Main {
    public static void main(String[] args) {
        System.out.println(new Rectangle(3, 4).area());
        System.out.println(new Square(5).area());
    }
}
""", "12\n25"),
        ),
        exercise_id="ex-oop-rectangle",
    ),
)

LESSON_BY_ID: dict[str, Lesson] = {lesson.id: lesson for lesson in LESSONS}
