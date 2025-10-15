'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import { SearchBar } from '@/components/SearchBar';
import { Controls } from '@/components/Controls';
import { ResultCard } from '@/components/ResultCard';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { SearchSkeleton } from '@/components/SearchSkeleton';
import { search, SearchRequest } from '@/lib/api';
import { measureLatency, formatLatency } from '@/lib/time';

export default function HomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URLパラメータから初期値を取得
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [k, setK] = useState(parseInt(searchParams.get('k') || '5'));
  const [useMmr, setUseMmr] = useState(searchParams.get('mmr') === 'true');
  const [similarityMethod, setSimilarityMethod] = useState(searchParams.get('sim') || 'distance');
  const [latency, setLatency] = useState<number | null>(null);

  // URLパラメータを更新
  const updateUrl = (params: Partial<{ q: string; k: number; mmr: boolean; sim: string }>) => {
    const newParams = new URLSearchParams(searchParams);
    
    if (params.q !== undefined) {
      if (params.q) newParams.set('q', params.q);
      else newParams.delete('q');
    }
    if (params.k !== undefined) newParams.set('k', params.k.toString());
    if (params.mmr !== undefined) newParams.set('mmr', params.mmr.toString());
    if (params.sim !== undefined) newParams.set('sim', params.sim);
    
    router.replace(`?${newParams.toString()}`, { scroll: false });
  };

  // 検索実行
  const handleSearch = (searchQuery: string) => {
    setQuery(searchQuery);
    updateUrl({ q: searchQuery });
  };

  // パラメータ変更時のURL更新
  useEffect(() => {
    updateUrl({ k, mmr: useMmr, sim: similarityMethod });
  }, [k, useMmr, similarityMethod]);

  // React Queryで検索実行
  const searchRequest: SearchRequest = {
    query,
    k,
    use_mmr: useMmr,
    similarity_method: similarityMethod,
  };

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['search', query, k, useMmr, similarityMethod],
    queryFn: async () => {
      if (!query.trim()) {
        throw new Error('Query is empty');
      }
      
      const { result, latency: measuredLatency } = await measureLatency(() =>
        search(searchRequest)
      );
      
      setLatency(measuredLatency);
      return result;
    },
    enabled: !!query.trim(),
  });

  const results = data?.results || [];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">TTCDX Vendor RAG Search</h1>
          <p className="text-muted-foreground">
            ベンダー検索システム - 自然言語でベンダーを検索できます
          </p>
        </div>

        {/* 検索バー */}
        <div className="mb-6">
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder="例: AI開発会社、クラウドサービス、セキュリティソリューション"
          />
        </div>

        {/* コントロール */}
        <div className="mb-6">
          <Controls
            k={k}
            onKChange={setK}
            useMmr={useMmr}
            onMmrChange={setUseMmr}
            similarityMethod={similarityMethod}
            onSimilarityChange={setSimilarityMethod}
          />
        </div>

        {/* 検索結果 */}
        <div className="space-y-4">
          {isLoading && <SearchSkeleton />}
          
          {error && (
            <ErrorState
              error={error as Error}
              onRetry={() => refetch()}
            />
          )}
          
          {!isLoading && !error && results.length === 0 && query && (
            <EmptyState />
          )}
          
          {!isLoading && !error && results.length > 0 && (
            <div className="space-y-4">
              {results.map((result, index) => (
                <ResultCard
                  key={`${result.metadata.vendor_id}-${index}`}
                  result={result}
                  index={index}
                />
              ))}
            </div>
          )}
        </div>

        {/* フッター情報 */}
        {!isLoading && !error && results.length > 0 && (
          <div className="mt-8 pt-4 border-t text-sm text-muted-foreground">
            <div className="flex justify-between items-center">
              <span>{results.length}件の結果</span>
              {latency && (
                <span>検索時間: {formatLatency(latency)}</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
