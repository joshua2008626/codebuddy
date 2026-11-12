import type { Monaco } from "@monaco-editor/react";
import type { LangId } from "./languages";

/** Snippets offered through Monaco's completion list, on top of its built-in word completion. */
const SNIPPETS: Record<LangId, { label: string; detail: string; body: string }[]> = {
  python: [
    { label: "for", detail: "for loop over a range", body: "for ${1:i} in range(${2:n}):\n\t$0" },
    { label: "while", detail: "while loop", body: "while ${1:condition}:\n\t$0" },
    { label: "def", detail: "function", body: "def ${1:name}(${2:args}):\n\t$0" },
    { label: "if", detail: "if statement", body: "if ${1:condition}:\n\t$0" },
    { label: "ifmain", detail: "entry-point guard", body: 'if __name__ == "__main__":\n\t$0' },
    { label: "readint", detail: "read an integer from stdin", body: "${1:n} = int(input())" },
    { label: "readints", detail: "read a line of integers", body: "${1:nums} = list(map(int, input().split()))" },
  ],
  c: [
    { label: "main", detail: "main function", body: "int main(void) {\n\t$0\n\treturn 0;\n}" },
    { label: "for", detail: "for loop", body: "for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t$0\n}" },
    { label: "while", detail: "while loop", body: "while (${1:condition}) {\n\t$0\n}" },
    { label: "if", detail: "if statement", body: "if (${1:condition}) {\n\t$0\n}" },
    { label: "printf", detail: "print formatted text", body: 'printf("${1:%d}\\n", ${2:value});' },
    { label: "scanf", detail: "read formatted input", body: 'scanf("${1:%d}", &${2:variable});' },
    { label: "struct", detail: "struct definition", body: "struct ${1:Name} {\n\t$0\n};" },
  ],
  java: [
    { label: "main", detail: "main method", body: "public static void main(String[] args) {\n\t$0\n}" },
    { label: "sout", detail: "System.out.println", body: "System.out.println($0);" },
    { label: "fori", detail: "indexed for loop", body: "for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t$0\n}" },
    { label: "foreach", detail: "enhanced for loop", body: "for (${1:int} ${2:item} : ${3:items}) {\n\t$0\n}" },
    { label: "while", detail: "while loop", body: "while (${1:condition}) {\n\t$0\n}" },
    { label: "scanner", detail: "Scanner on stdin", body: "Scanner ${1:in} = new Scanner(System.in);" },
    { label: "class", detail: "class definition", body: "class ${1:Name} {\n\t$0\n}" },
  ],
};

let registered = false;

/** Runs once, before the first editor mounts: defines the two themes and registers snippet completions. */
export function setupMonaco(monaco: Monaco) {
  monaco.editor.defineTheme("codebuddy-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "A78BFA" },
      { token: "string", foreground: "22D3EE" },
      { token: "number", foreground: "FBBF24" },
      { token: "comment", foreground: "6B7694", fontStyle: "italic" },
      { token: "type", foreground: "7DD3FC" },
    ],
    colors: {
      "editor.background": "#0F1526",
      "editor.foreground": "#E6EAF5",
      "editorLineNumber.foreground": "#4B5675",
      "editorLineNumber.activeForeground": "#8B95B3",
      "editor.lineHighlightBackground": "#161E34",
      "editor.selectionBackground": "#8B5CF655",
      "editorCursor.foreground": "#22D3EE",
      "editorIndentGuide.background1": "#1D2640",
      "editorWidget.background": "#161E34",
      "editorSuggestWidget.background": "#161E34",
      "editorSuggestWidget.border": "#1D2640",
    },
  });

  monaco.editor.defineTheme("codebuddy-light", {
    base: "vs",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "6D40DC" },
      { token: "string", foreground: "0E7490" },
      { token: "number", foreground: "B46E00" },
      { token: "comment", foreground: "64748B", fontStyle: "italic" },
    ],
    colors: {
      "editor.background": "#FFFFFF",
      "editor.foreground": "#0F172A",
      "editorLineNumber.foreground": "#94A3B8",
      "editor.lineHighlightBackground": "#F1F5FB",
      "editorCursor.foreground": "#3454E0",
    },
  });

  if (registered) return; // registering twice would duplicate every suggestion
  registered = true;

  (Object.keys(SNIPPETS) as LangId[]).forEach((lang) => {
    monaco.languages.registerCompletionItemProvider(lang, {
      provideCompletionItems(model, position) {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };
        return {
          suggestions: SNIPPETS[lang].map((s) => ({
            label: s.label,
            kind: monaco.languages.CompletionItemKind.Snippet,
            detail: s.detail,
            insertText: s.body,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
          })),
        };
      },
    });
  });
}
