/**
 * レイテンシ計測ユーティリティ
 */
export function measureLatency<T>(
  fn: () => Promise<T>
): Promise<{ result: T; latency: number }> {
  const start = performance.now();
  
  return fn().then((result) => {
    const end = performance.now();
    return {
      result,
      latency: Math.round(end - start)
    };
  });
}

export function formatLatency(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
}
