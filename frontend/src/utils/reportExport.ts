import type { Language, ReviewResponse } from '../types';

export function buildMarkdownReport(data: ReviewResponse, language: Language, code: string): string {
  const lines: string[] = [
    `# CodeReview Report — ${language.toUpperCase()}`,
    '',
    `**Score:** ${data.score}/100`,
    `**Engine:** ${data.lint_engine ?? 'CodeReview Engine'}`,
    '',
    `## Summary`,
    data.summary,
    '',
  ];

  if (data.issue_stats) {
    lines.push(
      `**Errors:** ${data.issue_stats.error ?? 0} · **Warnings:** ${data.issue_stats.warning ?? 0} · **Info:** ${data.issue_stats.info ?? 0}`,
      ''
    );
  }

  if (data.issues.length) {
    lines.push('## Critical Issues', '');
    for (const i of data.issues) {
      lines.push(`### L${i.line ?? '?'} — ${i.title} (${i.severity})`);
      lines.push(i.message);
      if (i.suggestion) lines.push(`> Fix: ${i.suggestion}`);
      lines.push('');
    }
  }

  if (data.optimizations.length) {
    lines.push('## Optimizations', '');
    for (const o of data.optimizations) {
      lines.push(`- **${o.title}** (${o.impact} impact): ${o.description}`);
    }
    lines.push('');
  }

  if (data.best_practices.length) {
    lines.push('## Best Practices', '');
    for (const b of data.best_practices) {
      lines.push(`- L${b.line ?? '?'} ${b.title}: ${b.message}`);
    }
    lines.push('');
  }

  lines.push('## Source Code', '', '```' + language, code, '```', '');
  return lines.join('\n');
}

export function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
