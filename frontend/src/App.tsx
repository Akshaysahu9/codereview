import { useCallback, useEffect, useState } from 'react';
import { Cpu, Play, RotateCcw, Wifi, WifiOff } from 'lucide-react';
import clsx from 'clsx';
import { api } from './api/client';
import { CodeEditor } from './components/CodeEditor';
import { EmptyPanel, ErrorPanel, LoadingPanel, Sidebar } from './components/Layout';
import { HistoryPanel } from './components/HistoryPanel';
import { ExplainResults, FixResults, ReviewResults, TestsResults } from './components/Results';
import { LANGUAGE_OPTIONS, SAMPLE_CODE } from './data/samples';
import type {
  ExplainResponse,
  FixCodeResponse,
  GenerateTestsResponse,
  Language,
  ReviewResponse,
  Tab,
} from './types';

const ACTIONS: Record<Exclude<Tab, 'history'>, string> = {
  review: 'Analyze Code',
  explain: 'Explain',
  tests: 'Generate Tests',
  fix: 'Auto Fix',
};

const LANG_COLORS: Record<Language, string> = {
  python: 'from-yellow-500/20 to-yellow-600/5 border-yellow-500/30 text-yellow-300',
  javascript: 'from-amber-500/20 to-amber-600/5 border-amber-500/30 text-amber-300',
  typescript: 'from-blue-500/20 to-blue-600/5 border-blue-500/30 text-blue-300',
  java: 'from-orange-500/20 to-orange-600/5 border-orange-500/30 text-orange-300',
  cpp: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/30 text-cyan-300',
};

export default function App() {
  const [tab, setTab] = useState<Tab>('review');
  const [language, setLanguage] = useState<Language>('python');
  const [code, setCode] = useState(SAMPLE_CODE.python);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [engineName, setEngineName] = useState('CodeReview Engine');
  const [focusLine, setFocusLine] = useState<number | null>(null);

  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [explain, setExplain] = useState<ExplainResponse | null>(null);
  const [tests, setTests] = useState<GenerateTestsResponse | null>(null);
  const [fix, setFix] = useState<FixCodeResponse | null>(null);

  useEffect(() => {
    api.health()
      .then((h) => {
        setOnline(true);
        setEngineName(h.engine.name);
      })
      .catch(() => setOnline(false));
  }, []);

  const switchLanguage = (lang: Language) => {
    setLanguage(lang);
    setCode(SAMPLE_CODE[lang]);
    setReview(null);
    setExplain(null);
    setTests(null);
    setFix(null);
    setError(null);
  };

  const runAction = useCallback(async () => {
    if (!code.trim()) {
      setError('Paste or write code first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      if (tab === 'review') setReview(await api.review(code, language));
      else if (tab === 'explain') setExplain(await api.explain(code, language));
      else if (tab === 'tests') setTests(await api.generateTests(code, language));
      else if (tab === 'fix') {
        const r = review ?? (await api.review(code, language));
        if (!review) setReview(r);
        const fixable = [
          ...r.issues,
          ...r.best_practices.filter((i) => i.severity === 'error' || i.severity === 'warning'),
        ];
        setFix(await api.fix(code, language, fixable));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }, [code, language, tab, review]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && tab !== 'history' && !loading) {
        e.preventDefault();
        runAction();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [runAction, loading, tab]);

  const editorHighlights = (() => {
    if (!review) return [];
    const map = new Map<number, 'error' | 'warning' | 'info'>();
    const rank = { error: 3, warning: 2, info: 1 };
    for (const i of [...review.issues, ...review.best_practices]) {
      if (!i.line) continue;
      const sev = i.severity === 'error' ? 'error' : i.severity === 'warning' ? 'warning' : 'info';
      const prev = map.get(i.line);
      if (!prev || rank[sev] > rank[prev]) map.set(i.line, sev);
    }
    return [...map.entries()].map(([line, severity]) => ({ line, severity }));
  })();

  const loc = code.split('\n').length;
  const isSampleCode = code.trim() === SAMPLE_CODE[language].trim();
  const sampleNote =
    language === 'cpp'
      ? 'Sample C++ code is correct — expect a high score with no false errors.'
      : 'Demo sample has intentional bugs — low score means the engine is working correctly.';

  const results = () => {
    if (tab === 'history') {
      return (
        <HistoryPanel
          onLoad={(c, lang, t) => {
            setCode(c);
            setLanguage(lang as Language);
            setTab(t);
            setReview(null);
          }}
        />
      );
    }
    if (loading) return <LoadingPanel message={`Running ${ACTIONS[tab as Exclude<Tab, 'history'>]}…`} />;
    if (error) return <ErrorPanel message={error} />;
    if (tab === 'review' && review) {
      return (
        <ReviewResults
          data={review}
          language={language}
          code={code}
          onJumpToLine={(line) => setFocusLine(line)}
        />
      );
    }
    if (tab === 'explain' && explain) return <ExplainResults data={explain} />;
    if (tab === 'tests' && tests) return <TestsResults data={tests} />;
    if (tab === 'fix' && fix) {
      return <FixResults data={fix} originalCode={code} onApply={(fixed) => { setCode(fixed); setFix(null); }} />;
    }
    return (
      <EmptyPanel
        title="Ready for deep analysis"
        subtitle={`Select ${language.toUpperCase()} code and hit "${ACTIONS[tab as Exclude<Tab, 'history'>]}" — powered by ${engineName} (100% offline).`}
      />
    );
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar active={tab} onChange={(t) => { setTab(t); setError(null); }} />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 shrink-0 glass border-b border-slate-800/60 px-6 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">CodeReview</h1>
            <p className="text-xs text-slate-500">Static analysis for 5 languages</p>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap justify-center">
            {LANGUAGE_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => switchLanguage(value)}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-xs font-medium border bg-gradient-to-b transition-all',
                  language === value ? LANG_COLORS[value] : 'border-slate-800 text-slate-500 hover:border-slate-600'
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              <Cpu className="w-3 h-3" />
              {engineName}
            </span>
            <span className={clsx('flex items-center gap-1.5 text-xs', online ? 'text-emerald-400' : 'text-red-400')}>
              {online ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              {online ? 'API online' : 'API offline'}
            </span>
            {tab !== 'history' && (
              <>
                <button
                  onClick={() => setCode(SAMPLE_CODE[language])}
                  className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80"
                  title="Reset sample"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <button
                  onClick={runAction}
                  disabled={loading || online === false}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-semibold glow-btn disabled:opacity-40 transition-all"
                >
                  <Play className="w-4 h-4 fill-current" />
                  {ACTIONS[tab as Exclude<Tab, 'history'>]}
                </button>
              </>
            )}
          </div>
        </header>

        <div className="flex-1 flex min-h-0 p-3 gap-3">
          <section className="flex-1 flex flex-col min-w-0 glass rounded-2xl overflow-hidden">
            <div className="px-4 py-2.5 border-b border-slate-800/50 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Editor</span>
              <span className="text-xs text-slate-600 font-mono">{loc} lines · {language} · Ctrl+Enter</span>
            </div>
            {isSampleCode && tab === 'review' && (
              <div className="px-4 py-2 text-xs text-amber-300/90 bg-amber-500/5 border-b border-amber-500/10">
                {sampleNote}
              </div>
            )}
            <div className="flex-1 min-h-0">
              <CodeEditor
                code={code}
                language={language}
                onChange={setCode}
                highlights={editorHighlights}
                focusLine={focusLine}
              />
            </div>
          </section>

          <section className="flex-1 flex flex-col min-w-0 glass rounded-2xl overflow-hidden">
            <div className="px-4 py-2.5 border-b border-slate-800/50">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                {tab === 'history' ? 'History' : 'Report'}
              </span>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">{results()}</div>
          </section>
        </div>
      </div>
    </div>
  );
}
