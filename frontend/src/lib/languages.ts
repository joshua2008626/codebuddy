/** Supported languages, their file extensions and starter templates. */
export type LangId = "python" | "c" | "java";

export interface LangConfig {
  id: LangId;
  label: string;
  /** Monaco language id (all three ship with Monaco's basic-languages). */
  monaco: string;
  ext: string;
  defaultName: string;
  template: string;
}

export const LANGS: Record<LangId, LangConfig> = {
  python: {
    id: "python",
    label: "Python",
    monaco: "python",
    ext: ".py",
    defaultName: "main.py",
    template: `# Welcome to CodeBuddy. Press Run to execute this file.
name = input("What's your name? ")
print(f"Hello, {name}!")
`,
  },
  c: {
    id: "c",
    label: "C",
    monaco: "c",
    ext: ".c",
    defaultName: "main.c",
    template: `#include <stdio.h>

int main(void) {
    char name[64];
    printf("What's your name? ");
    scanf("%63s", name);
    printf("Hello, %s!\\n", name);
    return 0;
}
`,
  },
  java: {
    id: "java",
    label: "Java",
    monaco: "java",
    ext: ".java",
    defaultName: "Main.java",
    // The public class must be named Main: the execution service compiles the file as Main.java.
    template: `import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        System.out.print("What's your name? ");
        String name = in.hasNext() ? in.next() : "friend";
        System.out.println("Hello, " + name + "!");
    }
}
`,
  },
};

export const LANG_LIST: LangConfig[] = [LANGS.python, LANGS.c, LANGS.java];

/** Returns the language for a file name based on its extension, or null if unsupported. */
export function langFromName(name: string): LangId | null {
  const lower = name.toLowerCase();
  for (const l of LANG_LIST) if (lower.endsWith(l.ext)) return l.id;
  return null;
}
