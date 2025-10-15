export type SearchRequest = {
  query: string;
  k?: number;
  use_mmr?: boolean;
  similarity_method?: 'distance' | string;
};

export type SearchResult = {
  text: string;
  score: number;
  metadata: {
    vendor_id: string;
    [k: string]: any;
  };
};

export type SearchResponse = {
  results: SearchResult[];
};

const BASE = process.env.NEXT_PUBLIC_API_BASE!;

export async function search(
  body: SearchRequest,
  signal?: AbortSignal
): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`HTTP ${res.status}: ${errorText}`);
  }

  return res.json();
}
