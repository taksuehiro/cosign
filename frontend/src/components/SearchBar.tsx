'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function SearchBar({ onSearch, isLoading, placeholder = "ベンダーを検索..." }: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className="pl-10 pr-20"
          aria-label="検索クエリ"
        />
        <Button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-1 top-1/2 -translate-y-1/2 h-8 px-4"
        >
          {isLoading ? '検索中...' : '検索'}
        </Button>
      </div>
    </form>
  );
}
