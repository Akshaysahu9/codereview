import { useEffect, useState } from 'react';
import { BarChart3, Clock, Trash2, ChevronRight } from 'lucide-react';
import { api } from '../api/client';
import type { HistoryItem, HistoryStats, Tab } from '../types';

interface Props {
  onLoad: (code: string, language: string, tab: Tab) => void;
}

export function HistoryPanel({ onLoad }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<HistoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [data, st] = await Promise.all([api.history(), api.historyStats()]);
      setItems(data.items);
      setStats(st);
    } catch {
      setItems([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const typeLabels: Record<string, string> = {
    review: 'Code Review',
    explain: 'Explain',
    tests: 'Unit Tests',
    fix: 'Fix Code',
  };

  const typeToTab: Record<string, Tab> = {
    review: 'review',
    explain: 'explain',
    tests: 'tests',
    fix: 'fix',
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 text-sm">Loading history...</div>;
  }

  return (
    <div className="h-full flex flex-col">
      {stats && (
        <div className="p-4 border-b border-slate-800/80 grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-surface-900 border border-slate-800 p-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <BarChart3 className="w-3.5 h-3.5" /> Total runs
            </div>
            <div className="text-2xl font-bold text-white mt-1">{stats.total_analyses}</div>
          </div>
          <div className="rounded-xl bg-surface-900 border border-slate-800 p-3">
            <div className="text-xs text-slate-500">Reviews</div>
            <div className="text-2xl font-bold text-indigo-300 mt-1">{stats.total_reviews}</div>
          </div>
          <div className="rounded-xl bg-surface-900 border border-slate-800 p-3">
            <div className="text-xs text-slate-500">Avg score</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {stats.average_score ?? '—'}
            </div>
          </div>
          {Object.keys(stats.by_language).length > 0 && (
            <div className="col-span-3 flex flex-wrap gap-2 pt-1">
              {Object.entries(stats.by_language).map(([lang, n]) => (
                <span key={lang} className="text-[10px] px-2 py-1 rounded-full bg-slate-800 text-slate-400 uppercase">
                  {lang}: {n}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Review History</h2>
        {items.length > 0 && (
          <button
            onClick={async () => {
              await api.clearHistory();
              setItems([]);
              setStats(null);
              load();
            }}
            className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear All
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {items.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-12">No reviews yet. Run your first analysis!</p>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => onLoad(item.code_snippet, item.language, typeToTab[item.review_type] || 'review')}
                className="w-full p-4 text-left hover:bg-slate-800/30 transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      {typeLabels[item.review_type] || item.review_type}
                    </span>
                    <span className="text-xs font-mono text-slate-500 uppercase">{item.language}</span>
                    {item.score != null && (
                      <span className="text-xs text-slate-400">Score: {item.score}</span>
                    )}
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400" />
                </div>
                <pre className="mt-2 text-xs font-mono text-slate-500 truncate">
                  {item.code_snippet.slice(0, 120)}...
                </pre>
                <div className="flex items-center gap-1 mt-2 text-xs text-slate-600">
                  <Clock className="w-3 h-3" />
                  {new Date(item.created_at).toLocaleString()}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
