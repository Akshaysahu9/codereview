import { useState } from 'react';
import clsx from 'clsx';
import { AlertCircle, CheckCircle2, Copy, Download, ShieldAlert, TrendingUp } from 'lucide-react';
import type { Issue, Language, ReviewResponse, Severity } from '../types';
import { buildMarkdownReport, downloadText } from '../utils/reportExport';
import { computeLineDiff } from '../utils/lineDiff';
import { ImpactBadge, ScoreRing, SeverityBadge } from './Badges';

function IssueCard({ issue, onJump }: { issue: Issue; onJump?: (line: number) => void }) {
  return (
    <button
      type="button"
      onClick={() => issue.line && onJump?.(issue.line)}
      disabled={!issue.line || !onJump}
      className={clsx(
        'w-full text-left rounded-lg border border-slate-800 bg-surface-900/80 p-4 space-y-2 transition-colors',
        issue.line && onJump && 'hover:border-indigo-500/40 hover:bg-indigo-500/5 cursor-pointer'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <SeverityBadge severity={issue.severity} />
          <span className="text-xs text-slate-500 uppercase tracking-wide">{issue.category.replace(/_/g, ' ')}</span>
          {issue.line && (
            <span className="text-xs font-mono text-indigo-400/80 bg-indigo-500/10 px-1.5 py-0.5 rounded">L{issue.line}</span>
          )}
          {issue.confidence != null && issue.confidence >= 0.8 && (
            <span className="text-[10px] text-green-400/70">{Math.round(issue.confidence * 100)}% confidence</span>
          )}
        </div>
      </div>
      <h4 className="font-medium text-slate-200">{issue.title}</h4>
      <p className="text-sm text-slate-400 leading-relaxed">{issue.message}</p>
      {issue.suggestion && (
        <div className="flex items-start gap-2 text-sm text-indigo-300/90 bg-indigo-500/5 rounded p-2 border border-indigo-500/10">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span><strong className="text-indigo-400">Fix:</strong> {issue.suggestion}</span>
        </div>
      )}
      {issue.code_snippet && (
        <pre className="text-xs font-mono bg-surface-950 rounded p-2 text-amber-300/80 overflow-x-auto border border-amber-500/10">{issue.code_snippet}</pre>
      )}
      {issue.line && onJump && (
        <p className="text-[10px] text-indigo-400/70">Click to jump to line {issue.line} in editor</p>
      )}
    </button>
  );
}

type Section = 'issues' | 'security' | 'complexity' | 'optimization' | 'practices' | 'passed';

export function ReviewResults({
  data,
  language,
  code,
  onJumpToLine,
}: {
  data: ReviewResponse;
  language: Language;
  code: string;
  onJumpToLine?: (line: number) => void;
}) {
  const [section, setSection] = useState<Section>('issues');
  const [filter, setFilter] = useState<Severity | 'all'>('all');
  const [copied, setCopied] = useState(false);
  const engine = data.lint_engine || (language === 'python' ? 'Ruff' : language === 'javascript' || language === 'typescript' ? 'ESLint' : `${language.toUpperCase()} Analyzer`);

  const securityItems = [...data.issues, ...data.best_practices].filter((i) => i.category === 'security');

  const filteredIssues = filter === 'all'
    ? data.issues
    : data.issues.filter((i) => i.severity === filter);

  const sections: { id: Section; label: string; count: number }[] = [
    { id: 'issues', label: 'Critical Issues', count: data.issues.length },
    { id: 'security', label: 'Security', count: securityItems.length },
    { id: 'complexity', label: 'Complexity', count: data.complexity.function_count },
    { id: 'optimization', label: 'Optimization', count: data.optimizations.length },
    { id: 'practices', label: 'Best Practices', count: data.best_practices.length },
    { id: 'passed', label: 'Passed', count: data.passed_checks.length },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="p-5 border-b border-slate-800/80 space-y-4">
        <div className="flex items-start gap-6">
          <ScoreRing score={data.score} />
          <div className="flex-1 text-left">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg font-semibold text-white">Analysis Report</h2>
              <span className="text-[10px] px-2.5 py-1 rounded-full border bg-slate-800/80 text-slate-300 border-slate-700 font-mono">
                {engine}{data.analysis_engine === 'static' ? ' · Offline' : ''}
              </span>
            </div>
            <p className="text-sm text-slate-300 mt-2 leading-relaxed">{data.summary}</p>
            <p className="text-xs text-slate-500 mt-2">
              Check Critical Issues first, then Best Practices and Optimization tabs. Score drops mainly for real bugs.
            </p>
            {data.issue_stats && (
              <div className="flex gap-3 mt-3 text-xs">
                <span className="text-red-400">{data.issue_stats.error ?? 0} errors</span>
                <span className="text-amber-400">{data.issue_stats.warning ?? 0} warnings</span>
                <span className="text-slate-500">{data.issue_stats.info ?? 0} info</span>
              </div>
            )}
            <div className="flex gap-2 mt-3">
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(buildMarkdownReport(data, language, code));
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300 hover:bg-slate-700"
              >
                <Copy className="w-3.5 h-3.5" />
                {copied ? 'Copied!' : 'Copy Report'}
              </button>
              <button
                type="button"
                onClick={() =>
                  downloadText(`codereview-${language}-${Date.now()}.md`, buildMarkdownReport(data, language, code))
                }
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/80 text-xs text-white hover:bg-indigo-500"
              >
                <Download className="w-3.5 h-3.5" />
                Export .md
              </button>
            </div>
          </div>
        </div>

        {data.critical_findings && data.critical_findings.length > 0 && data.issue_stats && (data.issue_stats.error ?? 0) > 0 && (
          <div className="rounded-lg bg-red-500/5 border border-red-500/20 p-3 text-left">
            <div className="flex items-center gap-2 text-red-400 text-xs font-medium mb-2">
              <ShieldAlert className="w-4 h-4" />
              Priority Findings
            </div>
            <ul className="space-y-1">
              {data.critical_findings.map((f, i) => (
                <li key={i} className="text-sm text-red-300/80 flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">•</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="flex gap-1 p-2 border-b border-slate-800/80 overflow-x-auto">
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => setSection(s.id)}
            className={clsx(
              'px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors',
              section === s.id
                ? 'bg-indigo-500/20 text-indigo-300'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            {s.label}
            {s.count > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-slate-800 text-xs">{s.count}</span>
            )}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {section === 'issues' && (
          <>
            <div className="flex gap-1 mb-2">
              {(['all', 'error', 'warning', 'info'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={clsx(
                    'px-2 py-1 rounded text-xs capitalize',
                    filter === f ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
            {filteredIssues.length ? filteredIssues.map((i, idx) => (
              <IssueCard key={idx} issue={i} onJump={onJumpToLine} />
            )) :
            <p className="text-sm text-slate-500 text-center py-8">No issues in this category.</p>}
          </>
        )}

        {section === 'security' && (
          securityItems.length ? securityItems.map((i, idx) => (
            <IssueCard key={idx} issue={i} onJump={onJumpToLine} />
          )) : (
            <p className="text-sm text-green-400/80 text-center py-8 flex items-center justify-center gap-2">
              <CheckCircle2 className="w-5 h-5" /> No security issues detected
            </p>
          )
        )}

        {section === 'complexity' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Cyclomatic', value: data.complexity.cyclomatic_complexity },
                { label: 'Lines of Code', value: data.complexity.lines_of_code },
                { label: 'Functions', value: data.complexity.function_count },
                { label: 'Max Function Lines', value: data.complexity.max_function_lines },
                { label: 'Max Nesting', value: data.complexity.max_nesting_depth },
                { label: 'Rating', value: data.complexity.rating.toUpperCase() },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-lg bg-surface-900 border border-slate-800 p-3">
                  <div className="text-xs text-slate-500">{label}</div>
                  <div className="text-xl font-semibold text-white mt-1 capitalize">{value}</div>
                </div>
              ))}
            </div>
            <ul className="space-y-1">
              {data.complexity.details.map((d, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-slate-400">
                  <TrendingUp className="w-4 h-4 text-indigo-400" />
                  {d}
                </li>
              ))}
            </ul>
          </div>
        )}

        {section === 'optimization' && (
          data.optimizations.length ? data.optimizations.map((o, i) => (
            <div key={i} className="rounded-lg border border-slate-800 bg-surface-900/80 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-slate-200">{o.title}</h4>
                <ImpactBadge impact={o.impact} />
              </div>
              <p className="text-sm text-slate-400">{o.description}</p>
              {o.before && o.after && (
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-red-500/5 border border-red-500/20 rounded p-2 text-red-300/80">
                    <span className="text-red-400 block mb-1">Before</span>
                    {o.before}
                  </div>
                  <div className="bg-green-500/5 border border-green-500/20 rounded p-2 text-green-300/80">
                    <span className="text-green-400 block mb-1">After</span>
                    {o.after}
                  </div>
                </div>
              )}
            </div>
          )) : <p className="text-sm text-slate-500 text-center py-8">No optimization suggestions.</p>
        )}

        {section === 'practices' && (
          data.best_practices.length ? data.best_practices.map((i, idx) => (
            <IssueCard key={idx} issue={i} onJump={onJumpToLine} />
          )) :
          <p className="text-sm text-slate-500 text-center py-8">All best practices checks passed.</p>
        )}

        {section === 'passed' && (
          <ul className="space-y-2">
            {data.passed_checks.map((c, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-green-400/90">
                <CheckCircle2 className="w-4 h-4" />
                {c}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export function ExplainResults({ data }: { data: import('../types').ExplainResponse }) {
  return (
    <div className="h-full overflow-y-auto p-5 space-y-5 text-left">
      <div>
        <h2 className="text-lg font-semibold text-white mb-2">Code Explanation</h2>
        <p className="text-sm text-slate-300 leading-relaxed">{data.explanation}</p>
      </div>

      {(data.time_complexity || data.space_complexity) && (
        <div className="grid grid-cols-2 gap-3">
          {data.time_complexity && (
            <div className="rounded-lg bg-surface-900 border border-slate-800 p-3">
              <div className="text-xs text-slate-500">Time Complexity</div>
              <div className="text-lg font-mono text-indigo-300 mt-1">{data.time_complexity}</div>
            </div>
          )}
          {data.space_complexity && (
            <div className="rounded-lg bg-surface-900 border border-slate-800 p-3">
              <div className="text-xs text-slate-500">Space Complexity</div>
              <div className="text-lg font-mono text-indigo-300 mt-1">{data.space_complexity}</div>
            </div>
          )}
        </div>
      )}

      {data.key_concepts.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-400 mb-2">Key Concepts</h3>
          <div className="flex flex-wrap gap-2">
            {data.key_concepts.map((c) => (
              <span key={c} className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 text-sm border border-indigo-500/20">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.line_by_line.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-400 mb-2">Line Overview</h3>
          <div className="space-y-1 font-mono text-xs">
            {data.line_by_line.map((l) => (
              <div key={l.line} className="flex gap-3 py-1 border-b border-slate-800/50">
                <span className="text-slate-600 w-8 shrink-0">{l.line}</span>
                <span className="text-slate-400">{l.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function TestsResults({ data }: { data: import('../types').GenerateTestsResponse }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(data.tests);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="text-left">
          <h2 className="text-lg font-semibold text-white">Generated Tests</h2>
          <p className="text-sm text-slate-400">
            Framework: <span className="text-indigo-300 font-mono">{data.framework}</span> · {data.test_count} test(s)
          </p>
        </div>
        <button
          onClick={copy}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
        >
          <Copy className="w-4 h-4" />
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      {data.coverage_notes.length > 0 && (
        <div className="px-4 py-2 bg-amber-500/5 border-b border-amber-500/10 text-xs text-amber-300/80">
          {data.coverage_notes.join(' ')}
        </div>
      )}
      <pre className="flex-1 overflow-auto p-4 text-sm font-mono text-slate-300 bg-surface-950">{data.tests}</pre>
    </div>
  );
}

export function FixResults({
  data,
  originalCode,
  onApply,
}: {
  data: import('../types').FixCodeResponse;
  originalCode: string;
  onApply: (code: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [view, setView] = useState<'fixed' | 'diff'>('diff');
  const diff = computeLineDiff(originalCode, data.fixed_code);
  const hasChanges = originalCode.trim() !== data.fixed_code.trim();

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-800/80 text-left">
        <h2 className="text-lg font-semibold text-white">Fixed Code</h2>
        <p className="text-sm text-slate-400 mt-1">{data.issues_addressed} issue(s) addressed by rule-based auto fix</p>
        <ul className="mt-2 space-y-1">
          {data.changes_summary.map((c, i) => (
            <li key={i} className="text-sm text-green-400/90 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              {c}
            </li>
          ))}
        </ul>
        <div className="flex gap-2 mt-3 flex-wrap">
          <button
            onClick={() => onApply(data.fixed_code)}
            disabled={!hasChanges}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors disabled:opacity-40"
          >
            Apply to Editor
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText(data.fixed_code);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition-colors"
          >
            {copied ? 'Copied!' : 'Copy Fixed Code'}
          </button>
          <div className="flex rounded-lg overflow-hidden border border-slate-700 ml-auto">
            <button
              onClick={() => setView('diff')}
              className={clsx('px-3 py-1.5 text-xs', view === 'diff' ? 'bg-indigo-600 text-white' : 'text-slate-400')}
            >
              Diff View
            </button>
            <button
              onClick={() => setView('fixed')}
              className={clsx('px-3 py-1.5 text-xs', view === 'fixed' ? 'bg-indigo-600 text-white' : 'text-slate-400')}
            >
              Full Code
            </button>
          </div>
        </div>
      </div>
      {view === 'fixed' ? (
        <pre className="flex-1 overflow-auto p-4 text-sm font-mono text-slate-300 bg-surface-950">{data.fixed_code}</pre>
      ) : (
        <div className="flex-1 overflow-auto p-4 font-mono text-xs bg-surface-950 space-y-0.5">
          {diff.map((d, i) => (
            <div
              key={i}
              className={clsx(
                'flex gap-2 px-2 py-0.5 rounded',
                d.type === 'add' && 'bg-green-500/10 text-green-300',
                d.type === 'remove' && 'bg-red-500/10 text-red-300 line-through',
                d.type === 'same' && 'text-slate-500'
              )}
            >
              <span className="w-6 shrink-0 text-slate-600">{d.type === 'add' ? '+' : d.type === 'remove' ? '-' : ' '}</span>
              <span className="w-8 shrink-0 text-slate-600">{d.lineNo}</span>
              <span>{d.text || ' '}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
