import {
  AlertTriangle,
  Code2,
  History,
  Lightbulb,
  Loader2,
  Shield,
  Sparkles,
  TestTube2,
  Wrench,
  Zap,
} from 'lucide-react';
import clsx from 'clsx';
import type { Tab } from '../types';

const tabs: { id: Tab; label: string; icon: typeof Code2 }[] = [
  { id: 'review', label: 'Review', icon: Shield },
  { id: 'explain', label: 'Explain', icon: Lightbulb },
  { id: 'tests', label: 'Tests', icon: TestTube2 },
  { id: 'fix', label: 'Fix', icon: Wrench },
  { id: 'history', label: 'History', icon: History },
];

export function Sidebar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <aside className="w-[72px] shrink-0 glass border-r border-slate-800/60 flex flex-col items-center py-4 gap-2">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/30">
        <Code2 className="w-5 h-5 text-white" />
      </div>
      {tabs.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          title={label}
          className={clsx(
            'w-12 h-12 rounded-xl flex flex-col items-center justify-center gap-0.5 transition-all',
            active === id
              ? 'bg-indigo-500/20 text-indigo-300 ring-1 ring-indigo-500/40'
              : 'text-slate-500 hover:text-slate-200 hover:bg-slate-800/60'
          )}
        >
          <Icon className="w-5 h-5" />
          <span className="text-[9px] font-medium">{label}</span>
        </button>
      ))}
    </aside>
  );
}

export function LoadingPanel({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-indigo-500/20" />
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400 absolute inset-0 m-auto" />
      </div>
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="m-4 flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/25">
      <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
      <div>
        <p className="font-medium text-red-300">Analysis failed</p>
        <p className="text-sm text-red-300/70 mt-1">{message}</p>
      </div>
    </div>
  );
}

export function EmptyPanel({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-10 text-center">
      <div className="w-20 h-20 rounded-2xl glass flex items-center justify-center mb-5">
        <Sparkles className="w-9 h-9 text-indigo-400/80" />
      </div>
      <h3 className="text-xl font-semibold text-white">{title}</h3>
      <p className="text-sm text-slate-400 mt-2 max-w-md leading-relaxed">{subtitle}</p>
      <div className="flex gap-4 mt-8 text-xs text-slate-500">
        <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" /> Real linters</span>
        <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> Bug detection</span>
      </div>
    </div>
  );
}
