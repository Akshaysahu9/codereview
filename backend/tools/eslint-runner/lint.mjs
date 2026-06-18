import { ESLint } from 'eslint';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage: node lint.mjs <file>');
  process.exit(2);
}

const eslint = new ESLint({
  overrideConfigFile: join(__dirname, 'eslint.config.js'),
});

try {
  const results = await eslint.lintFiles([filePath]);
  const messages = results.flatMap((r) =>
    r.messages.map((m) => ({
      ruleId: m.ruleId,
      message: m.message,
      line: m.line,
      column: m.column,
      severity: m.severity,
    }))
  );
  console.log(JSON.stringify(messages));
  process.exit(messages.some((m) => m.severity === 2) ? 1 : 0);
} catch (err) {
  console.log(JSON.stringify([{ ruleId: 'lint-error', message: err.message, line: 1, severity: 2 }]));
  process.exit(2);
}
