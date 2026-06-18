export type Language = 'python' | 'javascript' | 'typescript' | 'java' | 'cpp';

export type Severity = 'error' | 'warning' | 'info' | 'suggestion';

export interface Issue {
  category: string;
  severity: Severity;
  title: string;
  message: string;
  line?: number;
  column?: number;
  suggestion?: string;
  code_snippet?: string;
  confidence?: number;
}

export interface ReviewResponse {
  language: Language;
  score: number;
  summary: string;
  issues: Issue[];
  complexity: ComplexityMetric;
  optimizations: OptimizationSuggestion[];
  best_practices: Issue[];
  passed_checks: string[];
  analysis_engine?: string;
  lint_engine?: string;
  critical_findings?: string[];
  issue_stats?: Record<string, number>;
}

export interface ComplexityMetric {
  cyclomatic_complexity: number;
  lines_of_code: number;
  function_count: number;
  max_function_lines: number;
  max_nesting_depth: number;
  rating: string;
  details: string[];
}

export interface OptimizationSuggestion {
  title: string;
  description: string;
  impact: string;
  line?: number;
  before?: string;
  after?: string;
}

export interface ExplainResponse {
  explanation: string;
  time_complexity?: string;
  space_complexity?: string;
  key_concepts: string[];
  line_by_line: { line: number; text: string }[];
}

export interface GenerateTestsResponse {
  framework: string;
  tests: string;
  test_count: number;
  coverage_notes: string[];
}

export interface FixCodeResponse {
  fixed_code: string;
  changes_summary: string[];
  issues_addressed: number;
}

export interface HistoryStats {
  total_analyses: number;
  total_reviews: number;
  average_score: number | null;
  by_language: Record<string, number>;
  by_type: Record<string, number>;
}

export interface HealthResponse {
  status: string;
  service: string;
  engine: {
    name: string;
    version: string;
    offline: boolean;
    languages: string[];
  };
}

export interface HistoryItem {
  id: number;
  language: string;
  code_snippet: string;
  title?: string;
  review_type: string;
  result_json: string;
  score?: number;
  created_at: string;
}

export type Tab = 'review' | 'explain' | 'tests' | 'fix' | 'history';
