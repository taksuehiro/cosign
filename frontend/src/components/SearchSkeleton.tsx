'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';

export function SearchSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-6 w-24 bg-muted animate-pulse rounded" />
                <div className="h-5 w-16 bg-muted animate-pulse rounded" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-2">
              <div className="h-4 bg-muted animate-pulse rounded w-full" />
              <div className="h-4 bg-muted animate-pulse rounded w-4/5" />
              <div className="h-4 bg-muted animate-pulse rounded w-3/5" />
            </div>
            <div className="flex gap-1 mt-3">
              <div className="h-5 w-16 bg-muted animate-pulse rounded" />
              <div className="h-5 w-20 bg-muted animate-pulse rounded" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
