export type DiffLine = { type: 'same' | 'add' | 'remove'; text: string; lineNo?: number };

export function computeLineDiff(before: string, after: string): DiffLine[] {
  const a = before.split('\n');
  const b = after.split('\n');
  const result: DiffLine[] = [];
  const max = Math.max(a.length, b.length);

  for (let i = 0; i < max; i++) {
    const left = a[i];
    const right = b[i];
    if (left === right) {
      if (left !== undefined) result.push({ type: 'same', text: left, lineNo: i + 1 });
    } else {
      if (left !== undefined) result.push({ type: 'remove', text: left, lineNo: i + 1 });
      if (right !== undefined) result.push({ type: 'add', text: right, lineNo: i + 1 });
    }
  }
  return result;
}
