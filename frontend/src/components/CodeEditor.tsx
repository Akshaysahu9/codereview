import { useEffect, useRef } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import type { Language } from '../types';

const LANG_MAP: Record<Language, string> = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  java: 'java',
  cpp: 'cpp',
};

export type LineHighlight = { line: number; severity: 'error' | 'warning' | 'info' };

interface Props {
  code: string;
  language: Language;
  onChange: (value: string) => void;
  readOnly?: boolean;
  height?: string;
  highlights?: LineHighlight[];
  focusLine?: number | null;
}

export function CodeEditor({
  code,
  language,
  onChange,
  readOnly,
  height = '100%',
  highlights = [],
  focusLine,
}: Props) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null);
  const decoRef = useRef<string[]>([]);

  const onMount: OnMount = (ed, monaco) => {
    editorRef.current = ed;
    monacoRef.current = monaco;
  };

  useEffect(() => {
    const ed = editorRef.current;
    const monaco = monacoRef.current;
    if (!ed || !monaco) return;

    const classFor = (s: LineHighlight['severity']) =>
      s === 'error' ? 'editor-line-error' : s === 'warning' ? 'editor-line-warning' : 'editor-line-info';

    const newDecos = highlights.map((h) => ({
      range: new monaco.Range(h.line, 1, h.line, 1),
      options: {
        isWholeLine: true,
        className: classFor(h.severity),
        glyphMarginClassName: h.severity === 'error' ? 'editor-glyph-error' : 'editor-glyph-warning',
      },
    }));

    decoRef.current = ed.deltaDecorations(decoRef.current, newDecos);
  }, [highlights, code]);

  useEffect(() => {
    const ed = editorRef.current;
    if (!ed || !focusLine) return;
    ed.revealLineInCenter(focusLine);
    ed.setPosition({ lineNumber: focusLine, column: 1 });
    ed.focus();
  }, [focusLine]);

  return (
    <Editor
      height={height}
      language={LANG_MAP[language]}
      value={code}
      onChange={(v) => onChange(v ?? '')}
      onMount={onMount}
      theme="vs-dark"
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: 'JetBrains Mono, monospace',
        lineNumbers: 'on',
        glyphMargin: true,
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 12, bottom: 12 },
        roundedSelection: true,
        cursorBlinking: 'smooth',
        smoothScrolling: true,
        tabSize: 4,
      }}
    />
  );
}
