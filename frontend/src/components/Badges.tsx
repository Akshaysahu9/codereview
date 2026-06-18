import clsx from 'clsx';
import type { Severity } from '../types';

const styles: Record<Severity, string> = {
  error: 'bg-red-500/10 text-red-400 border-red-500/30',
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  info: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  suggestion: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={clsx('inline-flex px-2 py-0.5 rounded text-xs font-medium border capitalize', styles[severity])}>
      {severity}
    </span>
  );
}

export function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444';
  const label = score >= 90 ? 'Excellent' : score >= 75 ? 'Good' : score >= 50 ? 'Needs fixes' : 'Critical';
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-28 h-28">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{score}</span>
        <span className="text-[10px] text-slate-400">{label}</span>
      </div>
    </div>
  );
}

export function ImpactBadge({ impact }: { impact: string }) {
  const colors: Record<string, string> = {
    high: 'text-red-400 bg-red-500/10',
    medium: 'text-amber-400 bg-amber-500/10',
    low: 'text-green-400 bg-green-500/10',
  };
  return (
    <span className={clsx('px-2 py-0.5 rounded text-xs font-medium capitalize', colors[impact] || colors.low)}>
      {impact} impact
    </span>
  );
}
