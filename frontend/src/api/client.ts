import type {
  ExplainResponse,
  FixCodeResponse,
  GenerateTestsResponse,
  HealthResponse,
  HistoryItem,
  HistoryStats,
  Issue,
  Language,
  ReviewResponse,
} from '../types';

const API_ROOT = import.meta.env.VITE_API_URL ?? '';
const BASE = API_ROOT ? `${API_ROOT.replace(/\/$/, '')}/api` : '/api';

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: async (): Promise<HealthResponse> => {
    const res = await fetch(`${BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  review: (code: string, language: Language, title?: string) =>
    post<ReviewResponse>('/review', { code, language, title }),

  explain: (code: string, language: Language, focus?: string) =>
    post<ExplainResponse>('/explain', { code, language, focus }),

  generateTests: (code: string, language: Language, framework?: string) =>
    post<GenerateTestsResponse>('/generate-tests', { code, language, framework }),

  fix: (code: string, language: Language, issues?: Issue[]) =>
    post<FixCodeResponse>('/fix', { code, language, issues }),

  history: async (): Promise<{ items: HistoryItem[]; total: number }> => {
    const res = await fetch(`${BASE}/history`);
    if (!res.ok) throw new Error('Failed to load history');
    return res.json();
  },

  historyStats: async (): Promise<HistoryStats> => {
    const res = await fetch(`${BASE}/history/stats`);
    if (!res.ok) throw new Error('Failed to load stats');
    return res.json();
  },

  deleteHistory: async (id: number) => {
    await fetch(`${BASE}/history/${id}`, { method: 'DELETE' });
  },

  clearHistory: async () => {
    await fetch(`${BASE}/history`, { method: 'DELETE' });
  },
};
