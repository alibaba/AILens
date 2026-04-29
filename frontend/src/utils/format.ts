/** Format milliseconds to "Xm Ys" or "Xs" */
export function formatDuration(ms: number): string {
  if (ms <= 0) return '0s';
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) return `${seconds}s`;
  return `${minutes}m ${seconds}s`;
}

/** Format percentage with 2 decimals, clamped to [0, 100]% */
export function formatPct(value: number): string {
  const clamped = Math.min(1, Math.max(0, value));
  return `${(clamped * 100).toFixed(2)}%`;
}
