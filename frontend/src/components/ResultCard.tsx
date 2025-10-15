'use client';

import { ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SearchResult } from '@/lib/api';

interface ResultCardProps {
  result: SearchResult;
  index: number;
}

export function ResultCard({ result, index }: ResultCardProps) {
  const { text, score, metadata } = result;
  const { vendor_id, type, website, ...otherMetadata } = metadata;

  // メタデータから表示するタグを抽出
  const displayTags = Object.entries(otherMetadata)
    .filter(([key, value]) => 
      value && 
      typeof value === 'string' && 
      value.length > 0 &&
      !['name', 'description'].includes(key)
    )
    .slice(0, 3); // 最大3つまで表示

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg">{vendor_id}</h3>
            <Badge variant="secondary" className="text-xs">
              {score.toFixed(3)}
            </Badge>
          </div>
          {website && (
            <a
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-primary transition-colors"
              aria-label={`${vendor_id}のウェブサイトを開く`}
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-muted-foreground line-clamp-3 mb-3">
          {text}
        </p>
        {displayTags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {displayTags.map(([key, value]) => (
              <Badge key={key} variant="outline" className="text-xs">
                {key}: {value}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
