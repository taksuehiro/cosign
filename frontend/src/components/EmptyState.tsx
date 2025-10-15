'use client';

import { Search } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Search className="h-12 w-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">検索結果が見つかりませんでした</h3>
      <p className="text-muted-foreground">
        別のキーワードで検索してみてください
      </p>
    </div>
  );
}
